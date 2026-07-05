# Master Every Technology: Data Engineering Job Hunter (Volume 3)

Welcome to the final volume! We will now cover the Deployment/DevOps infrastructure, Project Architecture, and finish with a top-to-bottom Code Walkthrough.

---

# 8. Streamlit Dashboard

**What is it?**  
Streamlit is an open-source Python framework that turns data scripts into shareable web apps in minutes. No HTML, CSS, or JS required.

**Why do we need it?**  
We have a SQLite database and a CSV file full of jobs. Staring at raw data is difficult. We need a visual UI to filter, search, and view charts.

**Why is it better than alternatives?**  
- *Streamlit vs Flask/Django*: Flask requires you to write HTML templates, build REST APIs, and manage frontend state. Streamlit handles all frontend rendering automatically based on pure Python logic, saving massive amounts of developer time.

**How does it work internally?**  
Streamlit runs the entire Python script from top to bottom every time a user interacts with a widget (like moving a slider). To prevent this from being terribly slow, it uses `@st.cache_data` to cache expensive computations (like loading the SQLite database) in memory.

**How is it used inside THIS project?**  
`job_hunter/dashboard/app.py` is our frontend. It loads data from `jobs.db`, calculates KPIs (Total Jobs, Remote %), displays a Plotly chart of Top Companies, and renders a data table using `st.dataframe`.

**Best Practices applied**: We implemented `st.column_config.LinkColumn` and `ProgressColumn` to make the UI interactive and highly readable.

---

# 9. Docker

## 9.1 Images, Containers & Volumes

**What is it?**  
Docker allows you to package an application and all its dependencies (Python, Playwright, OS libraries) into a standardized unit called a Container.

**Why do we need it?**  
Playwright requires heavy system dependencies (`libnss3`, `libasound2`, etc.). If you try to run this code on a bare Ubuntu server or a Windows machine, it will likely fail due to missing libraries ("It works on my machine" syndrome). Docker ensures it runs identically everywhere.

**How is it used inside THIS project?**  
- `Dockerfile`: The blueprint. It starts with Python 3.12, installs `requirements.txt`, and uses `playwright install-deps` to get all OS dependencies.
- `docker-compose.yml`: An orchestrator that runs the scraper and the Streamlit dashboard as two separate services, mounting a shared local volume `./data:/app/data` so both containers share the same SQLite database.

**Interview Questions**  
- *Beginner*: What is the difference between an Image and a Container?
- *Advanced*: Explain Layer Caching in a Dockerfile and why `COPY requirements.txt` is done before `COPY . .`. *(Answer: If code changes but requirements don't, Docker reuses the pip install cache, speeding up builds).*

---

# 10. GitHub Actions

## 10.1 CI/CD & Automated Schedulers

**What is it?**  
GitHub Actions is a CI/CD (Continuous Integration / Continuous Deployment) platform that automates software workflows right in your GitHub repository.

**Why do we need it?**  
We want our bot to scrape jobs every hour. We could run it locally (requiring our PC to be on 24/7), pay for an AWS server, or use GitHub Actions to run the script completely for free on Microsoft's servers using a `cron` schedule.

**How is it used inside THIS project?**  
`.github/workflows/schedule.yml` tells GitHub to boot up an Ubuntu server (`runs-on: ubuntu-latest`), install Python, cache the pip dependencies, inject our Secrets (API keys), run `main_job.py`, and finally `git push` the newly generated `jobs.db` and CSV back to the repository.

---

# 11. Configuration & Project Architecture

## 11.1 `.env` & Pydantic Settings

**Why do we need it?**  
Never hardcode API keys or passwords in code. If pushed to GitHub, bots will steal them in seconds.

**How is it used?**  
We use `pydantic-settings` in `job_hunter/config/settings.py`. It reads the `.env` file, validates that variables like `EMAIL` exist, and exposes them as Python objects (`settings.email`).

## 11.2 SOLID Principles & Modular Design

**Why this structure?**  
We separated the project into modules: `config`, `dashboard`, `database`, `email`, `processors`, and `scrapers`.
- **Single Responsibility Principle**: The scraper *only* scrapes. The `DataCleaner` *only* cleans. The `LLMProcessor` *only* scores. 
- If OpenAI changes its API, we only edit `llm_processor.py`. If we want to scrape a new site, we just add a file in `scrapers/`.

---

# 12. Full Code Walkthrough

Let's trace the exact execution flow of the system.

### Step 1: The Trigger
At 7 PM IST, GitHub Actions reads `schedule.yml` and executes `python main_job.py`.

### Step 2: Orchestration (`main_job.py`)
`run_job_hunter()` starts. 
- It first calls `init_db()` (from `db.py`) which uses SQLAlchemy to ensure the `jobs` table exists in `data/jobs.db`.
- It instantiates a list of scraper objects (`LinkedInScraper`, `YCPlaywrightScraper`, etc.).

### Step 3: Extraction (`scrapers/`)
The orchestrator loops through the scrapers calling `.fetch_jobs()`. 
- Inside `yc_scraper.py`, Playwright spins up a headless Chromium browser, navigates to the page, waits for JavaScript to render, extracts text using CSS selectors, and returns a list of raw dictionaries.

### Step 4: Transformation & Cleaning (`data_cleaner.py`)
The orchestrator passes the massive list of raw dictionaries to `DataCleaner.clean_jobs(raw_jobs)`.
- A Pandas DataFrame is created.
- HTML tags are regex-stripped from descriptions. Locations are capitalized.
- `drop_duplicates` removes jobs with the exact same company and title.

### Step 5: Database Pre-Filtering (`db.py`)
To save OpenAI API costs, we pass the cleaned jobs to `db_manager.filter_new_jobs()`.
- SQLAlchemy does a bulk `IN` query to check which `job_ids` already exist.
- It returns only the *brand new* jobs.

### Step 6: AI Enrichment (`llm_processor.py`)
The new jobs are passed to `LLMProcessor.process_jobs()`.
- It constructs a prompt combining your preset Resume and the job description.
- It calls Gemini/OpenAI, instructing it to return JSON.
- The robust `try/except` block parses the JSON and attaches the `resume_match_score` and `summary` to the job dictionary.

### Step 7: Database Storage (`db.py`)
The heavily enriched jobs are handed back to `db_manager.save_jobs()`.
- SQLAlchemy safely executes `INSERT` statements.
- It then dumps the entire database out to `jobs.csv` and `jobs.json`.

### Step 8: Alerting (`sender.py`)
The orchestrator loops through the new jobs. If `is_dream_job()` returns True (score > 80, Fresher, Remote/Mumbai), `EmailSender().send_dream_job_alert()` immediately fires an SMTP HTML email to you.
- Finally, if it is exactly 7 PM IST, it fetches all jobs scraped today and sends a batch report email with the CSV attached.

### Step 9: The Dashboard (`app.py`)
When you want to view the data, you open Streamlit.
- `app.py` directly reads the SQLite database, throws it into a Pandas DataFrame, calculates metrics, and displays beautiful Plotly charts and an interactive table.

---

**Congratulations!** You now understand the entire architecture, from the OS-level Docker dependencies down to the individual Pandas vectorization logic. You are ready to discuss every architectural decision in this project at a Senior Data Engineering level.
