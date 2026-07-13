import sys
import os

from job_hunter.database.models import init_db
from job_hunter.database.db import db_manager
from job_hunter.email.sender import EmailSender
from job_hunter.utils.news_fetcher import NewsFetcher
from job_hunter.utils.logger import setup_logger

logger = setup_logger(__name__)

def main():
    logger.info("Initializing Database...")
    init_db()

    logger.info("Fetching today's jobs...")
    todays_jobs = db_manager.get_todays_jobs()
    
    logger.info(f"Found {len(todays_jobs)} jobs. Fetching latest Data Engineering news...")
    news = NewsFetcher.get_latest_news(limit=3)
    
    logger.info("Sending report...")
    email_sender = EmailSender()
    email_sender.send_report(todays_jobs)
    if news:
        email_sender.send_news_newsletter(news)
        
    if not todays_jobs:
        logger.info("Sent empty job report because 0 jobs were found.")
        
    logger.info("Done sending email!")

if __name__ == "__main__":
    main()
