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
from job_hunter.processors.data_cleaner import DataCleaner
from job_hunter.processors.llm_processor import LLMProcessor
from job_hunter.database.db import db_manager
from job_hunter.email.sender import EmailSender
from job_hunter.utils.logger import setup_logger

logger = setup_logger(__name__)


def is_dream_job(job: dict) -> bool:
    score = job.get("resume_match_score", 0)
    if isinstance(score, str):
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
        # We want to send the report around 7 PM IST (13:30 UTC).
        # We will send it if the current UTC hour is >= 13, AND we haven't sent it today.
        
        last_report_file = os.path.join(data_dir, "last_report_date.txt")
        last_report_date = ""
        if os.path.exists(last_report_file):
            with open(last_report_file, "r") as f:
                last_report_date = f.read().strip()
                
        current_date = now_utc.strftime("%Y-%m-%d")

        if now_utc.hour >= 13 and last_report_date != current_date:
            logger.info("It's past 6:30 PM IST and no report sent today. Sending daily batch report to all recipients...")
            todays_jobs = db_manager.get_todays_jobs()
            if todays_jobs:
                email_sender = EmailSender()
                email_sender.send_report(todays_jobs)
                # Mark as sent
                with open(last_report_file, "w") as f:
                    f.write(current_date)
            else:
                logger.info("No jobs found today to send in the daily report.")
        else:
            if last_report_date == current_date:
                logger.info("Daily report already sent for today.")
            else:
                logger.info(f"Skipping daily report for now. It will be sent after 6:30 PM IST. (Current UTC hour: {now_utc.hour})")


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
