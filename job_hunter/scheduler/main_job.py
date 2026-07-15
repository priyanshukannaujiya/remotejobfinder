import sys
import os
import datetime
import re

# Add parent dir to path so we can run directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from job_hunter.database.models import init_db, data_dir
from job_hunter.scrapers.yc_scraper import YCPlaywrightScraper
from job_hunter.scrapers.linkedin_scraper import LinkedInScraper
from job_hunter.scrapers.indeed_scraper import IndeedScraper
from job_hunter.scrapers.wellfound_scraper import WellfoundScraper
from job_hunter.scrapers.glassdoor_scraper import GlassdoorScraper
from job_hunter.scrapers.google_scraper import GoogleJobsScraper
from job_hunter.processors.data_cleaner import DataCleaner
from job_hunter.processors.llm_processor import LLMProcessor
from job_hunter.database.db import db_manager
from job_hunter.email.sender import EmailSender
from job_hunter.utils.news_fetcher import NewsFetcher
from job_hunter.utils.logger import setup_logger

logger = setup_logger(__name__)


def is_dream_job(job: dict) -> bool:
    score = job.get("resume_match_score", 0)
    if score is None:
        score = 0
    elif isinstance(score, str):
        try:
            score = int(score)
        except (ValueError, TypeError):
            score = 0

    if score < 80:
        return False

    location = str(job.get("location", "")).lower()
    is_target_location = (
        "mumbai" in location
        or "pune" in location
        or "remote" in location
        or job.get("remote") is True
    )

    if not is_target_location:
        return False

    exp = str(job.get("experience_required", "")).lower()
    title = str(job.get("title", "")).lower()
    desc = str(job.get("summary", "")).lower()

    is_fresher = (
        bool(re.search(r'\b(0|1)\b', exp))
        or any(word in exp for word in ["fresher", "intern", "entry"])
        or any(word in title for word in ["fresher", "intern", "entry", "junior", "jr"])
        or job.get("internship") is True
    )

    return is_fresher


def run_job_hunter():
    logger.info("Initializing Database...")
    init_db()

    logger.info("Starting scrapers...")
    scrapers = [
        YCPlaywrightScraper(),
        LinkedInScraper(),
        IndeedScraper(),
        WellfoundScraper(),
        GlassdoorScraper(),
        GoogleJobsScraper(),
    ]

    try:
        raw_jobs = []
        for scraper in scrapers:
            try:
                logger.info(f"Running {scraper.__class__.__name__}...")
                scraped = scraper.fetch_jobs()
                raw_jobs.extend(scraped)
                logger.info(f"Found {len(scraped)} jobs from {scraper.__class__.__name__}")
            except Exception as e:
                logger.error(f"Error running scraper {scraper.__class__.__name__}: {e}")

        if not raw_jobs:
            logger.info("No jobs scraped today.")
            return

        logger.info("Cleaning jobs...")
        cleaned_jobs = DataCleaner.clean_jobs(raw_jobs)

        logger.info("Filtering out jobs already in the database...")
        new_jobs_to_process = db_manager.filter_new_jobs(cleaned_jobs)

        if not new_jobs_to_process:
            logger.info("No brand new jobs found this hour. Skipping LLM processing.")
        else:
            logger.info(f"Processing {len(new_jobs_to_process)} new jobs with LLM...")
            llm = LLMProcessor()
            processed_jobs = llm.process_jobs(new_jobs_to_process)

            email_sender = EmailSender()
            for job in processed_jobs:
                if is_dream_job(job):
                    logger.info(
                        f"Dream job found! {job.get('title')} at {job.get('company')}. Sending immediate alert."
                    )
                    email_sender.send_dream_job_alert(job)

            logger.info("Saving to database...")
            new_jobs_added = db_manager.save_jobs(processed_jobs)
            logger.info(f"Added {new_jobs_added} new unique jobs to the database.")

    finally:
        logger.info("Checking if it's time to send the daily report...")
        now_utc = datetime.datetime.utcnow()
        # Check and send News at 10:00 AM IST (now_utc.hour == 4)
        last_news_file = os.path.join(data_dir, "last_news_date.txt")
        last_news_date = ""
        if os.path.exists(last_news_file):
            with open(last_news_file, "r") as f:
                last_news_date = f.read().strip()
                
        # Check and send Jobs at 10:00 AM IST (now_utc.hour == 4)
        last_jobs_file = os.path.join(data_dir, "last_jobs_date.txt")
        last_jobs_date = ""
        if os.path.exists(last_jobs_file):
            with open(last_jobs_file, "r") as f:
                last_jobs_date = f.read().strip()

        current_date = now_utc.strftime("%Y-%m-%d")

        email_sender = EmailSender()

        # News logic (10:00 AM IST / hour >= 4)
        if now_utc.hour >= 4 and last_news_date != current_date:
            logger.info("It's past 10:00 AM IST. Fetching and sending Data Engineering news...")
            news = NewsFetcher.get_latest_news(limit=3)
            if news:
                email_sender.send_news_newsletter(news)
            with open(last_news_file, "w") as f:
                f.write(current_date)
        elif last_news_date != current_date:
            logger.info(f"Skipping news report for now. It will be sent after 10:00 AM IST. (Current UTC hour: {now_utc.hour})")
        else:
            logger.info("News report already sent for today.")
                
        # Jobs logic (10:00 AM IST / hour >= 4)
        if now_utc.hour >= 4 and last_jobs_date != current_date:
            logger.info("It's past 10:00 AM IST. Sending daily jobs batch report...")
            todays_jobs = db_manager.get_todays_jobs()
            email_sender.send_report(todays_jobs)
            if not todays_jobs:
                logger.info("Sent empty job report because 0 jobs were found.")
            with open(last_jobs_file, "w") as f:
                f.write(current_date)
        elif last_jobs_date != current_date:
            logger.info(f"Skipping jobs report for now. It will be sent after 10:00 AM IST. (Current UTC hour: {now_utc.hour})")
        else:
            logger.info("Jobs report already sent for today.")


if __name__ == "__main__":
    try:
        run_job_hunter()
    except Exception as e:
        logger.error(f"Critical error in main_job: {e}")
        try:
            import traceback
            from job_hunter.email.sender import EmailSender
            error_details = traceback.format_exc()
            email_sender = EmailSender()
            email_sender.send_failure_alert(error_details)
        except Exception as inner_e:
            logger.error(f"Failed to send failure email: {inner_e}")
        raise e
