from typing import List, Dict
from datetime import datetime
from .base import BaseScraper
from ..config.settings import settings
from ..database.db import db_manager


class GlassdoorScraper(BaseScraper):
    def __init__(self):
        super().__init__()

    def fetch_jobs(self) -> List[Dict]:
        jobs = []
        now = datetime.utcnow()
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
                )
                page = context.new_page()

                # Search for Data Engineer in India
                url = "https://www.glassdoor.co.in/Job/india-data-engineer-jobs-SRCH_IL.0,5_IN115_KO6,19.htm"
                page.goto(url, timeout=30000)

                # Handle login popup if it appears
                try:
                    page.wait_for_selector(".CloseButton", timeout=5000)
                    page.click(".CloseButton")
                except Exception:
                    pass

                page.wait_for_timeout(3000)

                # Job cards on Glassdoor often have 'jobCard' in the class
                job_cards = page.query_selector_all(
                    "li[class*='jobCard'], li[data-test='jobListing']"
                )

                new_jobs_for_url = 0
                for card in job_cards:
                    if new_jobs_for_url >= settings.max_jobs_per_source:
                        break
                        
                    title_elem = card.query_selector("a[data-test='job-title']")
                    company_elem = card.query_selector(
                        "span[data-test='employer-name']"
                    )
                    location_elem = card.query_selector("div[data-test='emp-location']")
                    link_elem = card.query_selector("a[data-test='job-title']")

                    if not title_elem:
                        # Fallback for different Glassdoor UI layouts
                        title_elem = card.query_selector(".JobCard_jobTitle___eLlk")
                        if not title_elem:
                            continue

                    title_text = title_elem.inner_text()
                    company_text = (
                        company_elem.inner_text() if company_elem else "Unknown"
                    )
                    location_text = (
                        location_elem.inner_text() if location_elem else "India"
                    )
                    href = link_elem.get_attribute("href") if link_elem else ""

                    full_link = (
                        f"https://www.glassdoor.co.in{href}"
                        if href and href.startswith("/")
                        else href
                    )
                    
                    job_id = self.generate_job_id("gd", company_text, title_text)
                    if db_manager.job_exists(job_id):
                        continue
                        
                    new_jobs_for_url += 1

                    jobs.append(
                        {
                            "job_id": job_id,
                            "company": self.clean_title(company_text),
                            "title": self.clean_title(title_text),
                            "location": location_text,
                            "remote": "remote" in location_text.lower()
                            or "remote" in title_text.lower(),
                            "internship": "intern" in title_text.lower(),
                            "experience_required": "Unknown",
                            "salary": None,
                            "skills": None,
                            "posting_date": now,
                            "apply_link": full_link or url,
                            "full_job_description": f"{title_text} at {company_text} in {location_text}",  # Glassdoor requires clicking to see desc, skipping to avoid popup walls
                            "source": "Glassdoor",
                            "timestamp": now,
                        }
                    )

                browser.close()
        except Exception as e:
            print(f"Glassdoor Playwright scraper error: {e}")

        return jobs
