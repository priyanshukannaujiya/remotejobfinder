import sys
import os

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
    print("Initializing Database...")
    init_db()
    
    print("Starting scrapers...")
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
            print(f"Running {scraper.__class__.__name__}...")
            scraped = scraper.fetch_jobs()
            raw_jobs.extend(scraped)
            print(f"Found {len(scraped)} jobs from {scraper.__class__.__name__}")
        except Exception as e:
            print(f"Error running scraper {scraper.__class__.__name__}: {e}")
            
    if not raw_jobs:
        print("No jobs scraped today.")
        return
        
    print("Cleaning jobs...")
    cleaned_jobs = DataCleaner.clean_jobs(raw_jobs)
    
    print("Processing with LLM...")
    llm = LLMProcessor()
    processed_jobs = llm.process_jobs(cleaned_jobs)
    
    email_sender = EmailSender()
    for job in processed_jobs:
        if is_dream_job(job):
            print(f"Dream job found! {job.get('title')} at {job.get('company')}. Sending immediate alert.")
            email_sender.send_dream_job_alert(job)
    
    print("Saving to database...")
    new_jobs_added = db_manager.save_jobs(processed_jobs)
    print(f"Added {new_jobs_added} new unique jobs to the database.")
    
    if new_jobs_added > 0:
        print("Sending email report...")
        email_sender = EmailSender()
        email_sender.send_report(processed_jobs) # Sending the jobs that were processed in this run
    else:
        print("No new jobs to email.")

if __name__ == "__main__":
    run_job_hunter()
