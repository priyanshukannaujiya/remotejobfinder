<div align="center">
  <h1>🚀 Automated Data Engineering Job Finder & AI Profile Matcher</h1>
  <p><strong>The Ultimate Data Engineering Job Scraper Powered by Python, Playwright, and LLMs (OpenAI / Gemini)</strong></p>
  <p><h3><a href="https://heypk4-dotcom.github.io/dataenginneringjob-finder/">🌐 Visit the Live Website</a> | <a href="https://dataenginneringjob-finder-4uexz3lf59hd5dauzymcph.streamlit.app/">📊 View Live Dashboard</a></h3></p>
</div>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/Streamlit-Dashboard-red.svg" alt="Streamlit">
  <img src="https://img.shields.io/badge/Docker-Supported-blue.svg" alt="Docker">
  <img src="https://img.shields.io/badge/GitHub_Actions-Automated-brightgreen.svg" alt="GitHub Actions">
  <img src="https://img.shields.io/badge/Playwright-Web_Scraping-orange.svg" alt="Playwright">
</p>

---

## 🌟 What is Data Engineering Job Finder?

**Data Engineering Job Finder** is an advanced, fully automated pipeline designed for job seekers who want to stop manually scrolling through job boards. Built exclusively for **Data Engineering**, **Analytics Engineering**, and **Big Data** roles, this system acts as your personal AI Recruiter.

### 🔥 Key Features for SEO & Scalability
- **Automated Job Scraper:** Headless scraping using **Playwright** and **BeautifulSoup** to extract jobs from modern React/Angular websites without getting blocked. Explicitly targets **Remote, Mumbai, and Pune** jobs, including **Internships**.
- **AI 'Master Profile' Matcher:** No resume upload required! Integrates with **OpenAI API**, **OpenRouter**, or **Google Gemini API** to read the job description, compare it against a *master-crafted AI Data Engineer profile*, and generate a match score (0-100).
- **SQLite Database:** Avoids duplicate applications by persisting jobs in a local SQLite DB using **SQLAlchemy ORM**.
- **Live Streamlit Dashboard:** A beautiful, responsive web UI hosted in the cloud to filter, search, and export jobs to CSV/JSON. Check it out here: [Live Dashboard](https://dataenginneringjob-finder-4uexz3lf59hd5dauzymcph.streamlit.app/)
- **Robust Automated Email Alerts:** Uses **SMTP** to instantly email you when a "Dream Job" (high match score, remote/Mumbai/Pune, fresher) is posted. Includes 3x automatic retries to handle transient network errors.
- **GitHub Actions Scheduler:** A 100% free CI/CD cron job that runs the scraper daily and pushes updates automatically. Fully resilient to GitHub Action timezone and queue delays!

---

## 🛠️ Step-by-Step Setup Guide

Whether you are using a standard IDE like **VS Code** or a highly advanced AI coding environment like **Antigravity**, here is everything you need to get the system running locally or in production.

### 1️⃣ Setting up Locally with VS Code

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/priyanshukannaujiya/remotejobfinder.git
   cd remotejobfinder
   ```

2. **Create a Python Virtual Environment:**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Mac/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies & Playwright Browsers:**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   playwright install-deps
   ```

### 2️⃣ Setting up with Antigravity IDE
If you are using the **Antigravity IDE** (AI-powered development), the setup is nearly instantaneous:
1. Open the repository folder in Antigravity.
2. Ask the agent: *"Set up the Data Engineering Job Finder environment."*
3. Antigravity will automatically detect `requirements.txt`, create the isolated environment, and install Playwright.
4. Provide your `.env` secrets when prompted, and the AI will configure the rest!

---

## 🔑 Understanding & Setting Up API Keys

This system relies on Environment Variables (`.env`) to keep your secrets safe. 

Create a file named `.env` in the root directory (copy from `.env.example`):

### Google Gmail App Password (For Email Alerts)
You cannot use your normal Gmail password for security reasons.
1. Go to your [Google Account Security settings](https://myaccount.google.com/security).
2. Enable **2-Step Verification**.
3. Search for **App Passwords**.
4. Create a new App Password (name it "JobScraper").
5. Copy the 16-character password into your `.env`:
   ```env
   EMAIL=your_email@gmail.com
   APP_PASSWORD=abcd efgh ijkl mnop
   ```

### OpenRouter vs Gemini API Keys
The system can use multiple LLMs. 
- **Google Gemini API**: Free tier available, great for fast processing.
  - Get it here: [Google AI Studio](https://aistudio.google.com/app/apikey)
- **OpenRouter API**: Aggregates models (GPT-4o, Claude 3.5 Sonnet, Llama 3). Highly recommended if you want the absolute best Resume Match Scores.
  - Get it here: [OpenRouter](https://openrouter.ai/)

Add them to your `.env`:
```env
GEMINI_API_KEYS=your_gemini_key_here
OPENROUTER_API_KEY=your_openrouter_key_here
```

---

## 🚀 Running the System

### Run the Pipeline Manually
To fetch jobs right now and trigger the LLM evaluation:
```bash
python -m job_hunter.scheduler.main_job
```

### Run the Streamlit Dashboard
To view your personalized jobs:
```bash
streamlit run job_hunter/dashboard/app.py
```
*(The dashboard runs on `http://localhost:8501`)*

---

## ⚙️ Automated Deployment

### 🐳 Docker Deployment
For a robust, isolated deployment on your own server (AWS EC2, DigitalOcean):
```bash
docker-compose up -d
```
This boots up a headless container that runs the cron scheduler and serves the Streamlit dashboard simultaneously.

### 🐙 GitHub Actions Scheduler (100% Free)
Don't want to pay for a server? Let GitHub run the script for you every day!

1. Go to your GitHub repository -> **Settings** -> **Secrets and Variables** -> **Actions**.
2. Click **New repository secret** and add your `.env` variables exactly as they are named (`EMAIL`, `APP_PASSWORD`, `GEMINI_API_KEYS`, `OPENROUTER_API_KEY`).
3. The `.github/workflows/schedule.yml` file is already configured. 
4. **How it works**: Every day at 10:00 AM IST, GitHub spins up an Ubuntu server, installs Python/Playwright, scrapes the jobs, scores them, emails you the report, and commits the updated database (`jobs.db`) back to your GitHub repository!

---

## 📊 Tech Stack Overview

- **Language:** Python 3.11+
- **Database:** SQLite & SQLAlchemy ORM
- **Data Engineering:** Pandas (Data Cleaning & Deduplication)
- **Web Scraping:** Playwright, BeautifulSoup, Requests
- **Frontend / UI:** Streamlit, Plotly
- **AI / NLP:** Google Generative AI, OpenAI SDK
- **DevOps:** Docker, Docker Compose, GitHub Actions CI/CD

---

<div align="center">
  <p><i>Stop searching for jobs. Let the jobs come to you.</i></p>
  <p>⭐ Don't forget to star the repository if this helped you! ⭐</p>
</div>
