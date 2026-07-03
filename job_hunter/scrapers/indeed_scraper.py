import time
from typing import List, Dict
from datetime import datetime
import uuid
from .base import BaseScraper
from ..config.settings import settings

class IndeedScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        
    def fetch_jobs(self) -> List[Dict]:
        jobs = []
        now = datetime.utcnow()
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                # Use a standard user agent to avoid basic blocks
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
                )
                page = context.new_page()
                
                # Search for Data Engineer in India (Remote)
                url = "https://in.indeed.com/jobs?q=Data+Engineer&l=Remote"
                page.goto(url, timeout=30000)
                
                # Wait for job cards to load
                try:
                    page.wait_for_selector(".job_seen_beacon", timeout=10000)
                except Exception:
                    print("Indeed jobs didn't load properly (possible captcha/block).")
                    
                job_cards = page.query_selector_all(".job_seen_beacon")
                
                for card in job_cards[:settings.max_jobs_per_source]:
                    title_elem = card.query_selector("h2.jobTitle span[title]")
                    company_elem = card.query_selector("[data-testid='company-name']")
                    location_elem = card.query_selector("[data-testid='text-location']")
                    link_elem = card.query_selector("h2.jobTitle a")
                    
                    if not title_elem or not link_elem:
                        continue
                        
                    title_text = title_elem.inner_text()
                    company_text = company_elem.inner_text() if company_elem else "Unknown"
                    location_text = location_elem.inner_text() if location_elem else "Remote"
                    href = link_elem.get_attribute("href")
                    
                    full_link = "https://in.indeed.com" + href if href.startswith("/") else href
                    
                    full_desc_text = f"{title_text} at {company_text}"
                    try:
                        job_page = context.new_page()
                        job_page.goto(full_link, timeout=15000)
                        desc_elem = job_page.query_selector("#jobDescriptionText")
                        if desc_elem:
                            full_desc_text = desc_elem.inner_text()
                        job_page.close()
                    except Exception as e:
                        print(f"Failed to fetch Indeed job description for {full_link}: {e}")
                    
                    jobs.append({
                        "job_id": f"ind_{uuid.uuid4().hex[:8]}",
                        "company": self.clean_title(company_text),
                        "title": self.clean_title(title_text),
                        "location": location_text,
                        "remote": "remote" in location_text.lower() or "remote" in title_text.lower(),
                        "internship": "intern" in title_text.lower(),
                        "experience_required": "Unknown",
                        "salary": None,
                        "skills": None,
                        "posting_date": now,
                        "apply_link": full_link,
                        "full_job_description": full_desc_text.strip()[:5000],
                        "source": "Indeed",
                        "timestamp": now
                    })
                    
                browser.close()
        except Exception as e:
            print(f"Indeed Playwright scraper error: {e}")
            
        return jobs
