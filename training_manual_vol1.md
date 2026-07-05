# Master Every Technology: Data Engineering Job Hunter (Volume 1)

Welcome to your mentorship program. As a Staff Data Engineer, I'm going to walk you through this project layer by layer. We will not just look at code; we will understand the *why* behind every architectural decision. 

Due to the massive scope of your request, this training manual is broken into volumes. **Volume 1** covers the foundational pillars: **Python, Web Scraping, and AI**.

---

# 1. Python Essentials

## 1.1 Virtual Environment & Pip

**What is it?**  
A Virtual Environment is an isolated container for your Python project. `pip` is the package manager used to install third-party libraries (like pandas, requests) into this container.

**Why do we need it?**  
If you install every package globally on your computer, projects will eventually have conflicting versions (e.g., Project A needs `pandas==1.0`, Project B needs `pandas==2.0`). Virtual environments prevent "Dependency Hell."

**Why is it better than alternatives?**  
Native `venv` + `pip` is built into Python. Alternatives like `conda` are great for data science but heavier. `poetry` is excellent for strict dependency locking in production, but `pip` + `requirements.txt` is the KISS (Keep It Simple, Stupid) standard for Dockerized apps.

**How does it work internally?**  
When you create a venv, it copies the Python executable and creates a local `site-packages` directory. When you activate it, it modifies your system's `PATH` environment variable so that typing `python` or `pip` points to the isolated folder, not the global system.

**How is it used inside THIS project?**  
You define your dependencies in `requirements.txt`. In GitHub Actions (`schedule.yml`) and Docker (`Dockerfile`), we run `pip install -r requirements.txt` to install these isolated packages.

**Industry Usage**  
Netflix and Airbnb use advanced package managers (like `Poetry` or `uv`), but the fundamental concept of isolated virtual environments applies universally across all tech giants.

**Interview Questions**  
- *Beginner*: What is a virtual environment?
- *Intermediate*: How does `pip` resolve dependencies?
- *Advanced*: Explain how `PATH` variables are manipulated when activating a venv.

**Practical Example**  
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install requests
```

**Common Mistakes**  
*Mistake*: Running `pip install` without activating the venv, polluting the global OS.
*Correction*: Always activate the environment or use Docker.

**Best Practices**  
Always freeze your dependencies using `pip freeze > requirements.txt` so builds are deterministic.

**Project Connection**  
Our `requirements.txt` acts as the blueprint for our isolated environment, ensuring the Docker container builds the exact same way every time.

---

## 1.2 Type Hints & Dataclasses

**What is it?**  
Type Hints (e.g., `def process(jobs: List[Dict]) -> List[Dict]:`) tell developers and linters what data types are expected.

**Why do we need it?**  
Python is dynamically typed. Without hints, a function `def calculate(a, b):` could take integers, lists, or strings. Type hints prevent runtime crashes by catching type mismatches during development.

**Why is it better than alternatives?**  
The alternative is "duck typing" (hoping the object acts correctly) or writing massive docstrings. Type hints allow IDEs (like VSCode) to provide autocomplete and tools like `mypy` to statically analyze code.

**How does it work internally?**  
At runtime, Python completely ignores type hints (they have zero performance impact). They are stored in the `__annotations__` dictionary of the function/class and read by static analysis tools.

**How is it used inside THIS project?**  
In `job_hunter/processors/data_cleaner.py`, we use `def clean_jobs(jobs: List[Dict]) -> List[Dict]:`. This explicitly tells anyone reading the code that it takes a list of dictionaries and returns a list of dictionaries.

**Industry Usage**  
Microsoft (which created TypeScript) heavily advocates for static typing. Uber and Instagram enforce strict `mypy` typing across millions of lines of Python code.

**Interview Questions**  
- *Beginner*: Does Python enforce type hints at runtime? (Answer: No).
- *Intermediate*: What is the difference between `List[str]` and `Tuple[str, int]`?
- *Advanced*: How do you use `typing.Optional` and `typing.Union`?

**Practical Example**  
```python
from typing import Optional

def get_user(user_id: int) -> Optional[str]:
    if user_id == 1:
        return "Alice"
    return None
```

**Common Mistakes**  
*Mistake*: Using `Dict` without specifying inner types.
*Correction*: Use `Dict[str, Any]` to be explicit about keys and values.

---

# 2. Web Scraping

## 2.1 Playwright vs Requests/BeautifulSoup

**What is it?**  
`Requests` fetches raw HTML over HTTP. `BeautifulSoup` parses that static HTML. `Playwright` is a full browser automation tool (like a robot operating Chrome).

**Why do we need it?**  
Many modern websites (like LinkedIn, Wellfound) use React/Angular. When you fetch them with `Requests`, you get a blank page with JavaScript. Playwright actually executes the JS, rendering the data before extracting it.

**Why is it better than alternatives?**  
- *Playwright vs Selenium*: Playwright is newer, asynchronous, heavily backed by Microsoft, and significantly faster/more reliable than Selenium's WebDriver protocol.
- *Requests vs HTTPX*: HTTPX supports async, but Requests is the battle-tested standard for synchronous, simple HTTP calls.

**How does it work internally?**  
Playwright communicates with the browser engine (Chromium, WebKit) via the Chrome DevTools Protocol (CDP) over WebSockets. It can intercept network requests, wait for specific DOM elements to render, and bypass basic bot protections.

**How is it used inside THIS project?**  
Look at `job_hunter/scrapers/yc_scraper.py` and `linkedin_scraper.py`. We use Playwright to launch a headless browser, navigate to the job boards, wait for the job cards to render via JS, and then extract the text.

**Industry Usage**  
Data Engineering teams at Google and Amazon use distributed scraping architectures. They often prefer API integrations, but when APIs aren't available, they use headless browsers routed through proxy networks to bypass Cloudflare.

**Interview Questions**  
- *Beginner*: Why can't BeautifulSoup scrape a React website?
- *Intermediate*: How do you handle pagination in Playwright?
- *Advanced*: How would you bypass rate limiting and CAPTCHAs while scraping?

**Practical Example**  
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://example.com")
    title = page.title()
    print(title)
    browser.close()
```

**Common Mistakes**  
*Mistake*: Not waiting for elements to load, leading to `TimeoutError`.
*Correction*: Always use `page.wait_for_selector('.job-card')` before trying to extract data.

**Project Connection**  
Because Data Engineering roles are highly competitive, we need real-time data from platforms that heavily rely on JavaScript (YC, Wellfound). Playwright is the only reliable way to guarantee we extract the actual job descriptions.

---

# 3. AI & LLM Integration

## 3.1 OpenAI API & Structured JSON Output

**What is it?**  
The OpenAI API allows us to programmatically send prompts to Large Language Models (LLMs) like GPT-4 or Gemini. "Structured JSON Output" forces the AI to reply in a strict, predictable JSON format instead of plain text.

**Why do we need it?**  
Job descriptions are messy, unstructured text. As Data Engineers, we need *structured* data (Columns: Salary, Skills, Match Score). The LLM acts as an incredibly smart Regex parser, extracting these exact fields from the raw text.

**Why is it better than alternatives?**  
- *LLMs vs Rule-based NLP (Regex/Spacy)*: Regex breaks easily if the job description format changes slightly. LLMs understand semantic context (e.g., "We offer 150k" = Salary).

**How does it work internally?**  
We send a prompt containing the Job Description and the User's Resume. The LLM processes the tokens. By defining a schema, the API constraints the LLM's probability generation to only output valid JSON keys and values.

**How is it used inside THIS project?**  
In `job_hunter/processors/llm_processor.py`, we construct a prompt containing your resume and the scraped job. We ask the LLM to return a JSON object with `resume_match_score`, `missing_skills`, etc. We then parse this JSON and attach it to the job dictionary before saving it to SQLite.

**Industry Usage**  
Databricks and Snowflake are heavily investing in LLM-powered ETL pipelines. Instead of writing complex parser scripts, they use LLMs to extract metadata, classify sentiment, and normalize schemas on the fly.

**Interview Questions**  
- *Beginner*: What is a prompt?
- *Intermediate*: How do you prevent an LLM from hallucinating data?
- *Advanced*: Explain how token limits and temperature affect an API call.

**Practical Example**  
```python
import json

prompt = "Extract salary from: 'Paying $120k for Data Engineer'. Return JSON with key 'salary'."
# Mock API response
response = '{"salary": "$120k"}' 
data = json.loads(response)
print(data['salary'])
```

**Common Mistakes**  
*Mistake*: Trusting the LLM to always output valid JSON.
*Correction*: Always use a `try...except json.JSONDecodeError:` block, as we did in our recent repository optimization, to prevent the pipeline from crashing.

**Project Connection**  
This is the "Brain" of the project. Without this, you just have a list of random jobs. With it, you have a highly personalized filter that calculates a `resume_match_score`, ensuring you only get emailed about your "Dream Jobs."

---

*This concludes Volume 1. Please review this material. When you are ready, ask for Volume 2, which will cover the Database Architecture (SQLite/SQLAlchemy), Pandas Data Engineering, and the Streamlit Dashboard.*
