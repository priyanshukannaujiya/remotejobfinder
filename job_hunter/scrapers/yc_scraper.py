from typing import List, Dict
from datetime import datetime
from .base import BaseScraper
from ..config.settings import settings
from ..database.db import db_manager


class YCPlaywrightScraper(BaseScraper):
    """
    A basic Playwright scraper for YCombinator jobs or similar platforms.
    """

    def __init__(self):
        super().__init__()
        # In a real scenario, you'd import sync_playwright and run it
        # from playwright.sync_api import sync_playwright

    def fetch_jobs(self) -> List[Dict]:
        jobs = []
        now = datetime.utcnow()
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto("https://news.ycombinator.com/jobs", timeout=30000)

                # HackerNews jobs is very simple HTML
                rows = page.query_selector_all("tr.athing")

                new_jobs_for_url = 0
                for row in rows:
                    if new_jobs_for_url >= settings.max_jobs_per_source:
                        break
                        
                    title_elem = row.query_selector(".titleline a")
                    if not title_elem:
                        continue

                    title_text = title_elem.inner_text()
                    link = title_elem.get_attribute("href")
                    if link and not link.startswith("http"):
                        link = "https://news.ycombinator.com/" + link

                    # Check post age to ensure it's recent (past 24 hours)
                    try:
                        next_row = row.evaluate_handle("el => el.nextElementSibling")
                        if next_row:
                            age_elem = next_row.as_element().query_selector(".age")
                            if age_elem:
                                age_text = age_elem.inner_text().lower()
                                # if it says '2 days ago' or '3 days ago', skip it
                                if "day" in age_text and not age_text.startswith(
                                    "1 day"
                                ):
                                    continue
                    except Exception:
                        pass  # Ignore parsing errors on age and continue safely

                    # Basic heuristic for Data Engineering
                    lower_title = title_text.lower()
                    if "data" in lower_title or "engineer" in lower_title:
                        job_id = self.generate_job_id("yc", "YC Startup", title_text)
                        if db_manager.job_exists(job_id):
                            continue
                            
                        new_jobs_for_url += 1
                        
                        # Fetch full job description by visiting the link
                        full_desc_text = title_text
                        try:
                            job_page = browser.new_page()
                            job_page.goto(link, timeout=15000)
                            # Extract all visible text from the page
                            full_desc_text = job_page.evaluate("document.body.innerText")
                            job_page.close()
                        except Exception as e:
                            print(f"Failed to fetch YC job description for {link}: {e}")

                        jobs.append(
                            {
                                "job_id": job_id,
                                "company": "YC Startup",  # HN jobs often have company in title
                                "title": self.clean_title(title_text),
                                "location": "Remote/US",  # Need LLM to extract this from text
                                "remote": "remote" in lower_title,
                                "internship": "intern" in lower_title,
                                "experience_required": "Unknown",
                                "salary": None,
                                "skills": None,
                                "posting_date": now,
                                "apply_link": link,
                                "full_job_description": full_desc_text.strip()[
                                    :5000
                                ],  # Pass up to 5k chars to LLM
                                "source": "YC HackerNews",
                                "timestamp": now,
                            }
                        )
                browser.close()
        except Exception as e:
            print(f"Playwright scraper error: {e}")

        return jobs
