import sys
import os
import datetime

# Add parent dir to path so we can run directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from job_hunter.database.models import init_db
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
    score = job.get('resume_match_score', 0)
    if isinstance(score, str):
        try:
            score = int(score)
        except:
            score = 0
            
    if score < 80:
        return False
        
    location = str(job.get('location', '')).lower()
    is_target_location = ('mumbai' in location or 
                          'pune' in location or 
                          'remote' in location or 
                          job.get('remote') == True)
                          
    if not is_target_location:
        return False
        
    exp = str(job.get('experience_required', '')).lower()
    title = str(job.get('title', '')).lower()
    
    is_fresher = any(word in exp for word in ['0', '1', 'fresher', 'intern', 'entry']) or \
                 any(word in title for word in ['fresher', 'intern', 'entry', 'junior', 'jr']) or \
                 job.get('internship') == True
                 
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
        GlassdoorScraper()
    ]
    
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
        logger.info("No brand new jobs found this hour. Exiting.")
        return
        
    logger.info(f"Processing {len(new_jobs_to_process)} new jobs with LLM...")
    llm = LLMProcessor()
    processed_jobs = llm.process_jobs(new_jobs_to_process)
    
    email_sender = EmailSender()
    for job in processed_jobs:
        if is_dream_job(job):
            logger.info(f"Dream job found! {job.get('title')} at {job.get('company')}. Sending immediate alert.")
            email_sender.send_dream_job_alert(job)
    
    logger.info("Saving to database...")
    new_jobs_added = db_manager.save_jobs(processed_jobs)
    logger.info(f"Added {new_jobs_added} new unique jobs to the database.")
    
    if new_jobs_added > 0:
        logger.info("Checking if it's time to send the daily report...")
        now_utc = datetime.datetime.utcnow()
        # 13:00 to 13:59 UTC corresponds to 18:30 to 19:29 IST. 
        # With cron '30 * * * *', this run is at 13:30 UTC (Exactly 7:00 PM IST)
        if now_utc.hour == 13:
            logger.info("It's 7 PM IST! Sending daily batch report to all recipients...")
            todays_jobs = db_manager.get_todays_jobs()
            if todays_jobs:
                email_sender = EmailSender()
                email_sender.send_report(todays_jobs)
        else:
            logger.info(f"Skipping daily report for now. It will be sent at 7 PM IST. (Current UTC hour: {now_utc.hour})")
    else:
        logger.info("No new jobs to email.")

if __name__ == "__main__":
    run_job_hunter()
