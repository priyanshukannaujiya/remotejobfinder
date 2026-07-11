import time
from typing import List, Dict
from datetime import datetime
from .base import BaseScraper
from ..config.settings import settings
from ..database.db import db_manager


class GoogleJobsScraper(BaseScraper):
    """
    Scrapes Google Jobs using Playwright.
    Google often blocks headless browsers with CAPTCHAs, so this is a best-effort scraper.
    """

    def __init__(self):
        super().__init__()
        self.search_url = "https://www.google.com/search?q=Data+Engineer+jobs+India&ibp=htl;jobs"

    def fetch_jobs(self) -> List[Dict]:
        jobs = []
        now = datetime.utcnow()
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                # Use a realistic user agent to lower the chance of CAPTCHA
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080},
                )
                page = context.new_page()
                page.goto(self.search_url, timeout=30000)

                # Wait for job list items to load
                try:
                    page.wait_for_selector('li[data-hveid]', timeout=10000)
                except Exception as e:
                    print(f"Google Jobs failed to load or got a CAPTCHA: {e}")
                    browser.close()
                    return jobs

                job_elements = page.query_selector_all('li[data-hveid]')
                
                for el in job_elements:
                    try:
                        title_el = el.query_selector('div[role="heading"]')
                        title = self.clean_title(title_el.inner_text()) if title_el else ""

                        # Extract full text to parse company and location
                        full_text = el.inner_text().split('\n')
                        full_text = [t.strip() for t in full_text if t.strip()]
                        
                        if len(full_text) < 3:
                            continue
                            
                        if not title:
                            title = self.clean_title(full_text[0])
                        
                        company = full_text[1]
                        location = full_text[2]
                        
                        job_id = self.generate_job_id("google", company, title)
                        if db_manager.job_exists(job_id):
                            continue

                        # Click the job to load the description panel
                        try:
                            el.click(timeout=3000)
                            time.sleep(1) # wait for the panel to update
                            # Grab all text from the body and look for typical description patterns
                            # A simple fallback is to just use the snippet visible on the card
                            summary = " ".join(full_text[3:10])
                        except Exception:
                            summary = " ".join(full_text[3:10])
                            
                        remote = "remote" in location.lower() or "remote" in title.lower()
                        internship = "intern" in title.lower()

                        job = {
                            "job_id": job_id,
                            "company": company,
                            "title": title,
                            "location": location,
                            "remote": remote,
                            "internship": internship,
                            "experience_required": "Fresher" if internship else "Not Specified",
                            "salary": "Not Specified",
                            "skills": "Not Specified",
                            "posting_date": now,
                            "apply_link": self.search_url,
                            "full_job_description": summary,
                            "source": "GoogleJobs",
                            "timestamp": now,
                        }
                        jobs.append(job)
                        
                        if len(jobs) >= settings.max_jobs_per_source:
                            break
                    except Exception as e:
                        print(f"Error parsing Google job item: {e}")
                        continue
                        
                browser.close()
        except ImportError:
            print("Playwright not installed, skipping Google scraper.")
        except Exception as e:
            print(f"Error in Google scraper: {e}")

        return jobs
