import time
from typing import List, Dict
from datetime import datetime
import uuid
from .base import BaseScraper
from ..config.settings import settings

class WellfoundScraper(BaseScraper):
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
                
                # Search for Data Engineer remote jobs
                url = "https://wellfound.com/role/l/data-engineer/remote"
                page.goto(url, timeout=30000)
                
                # Wait for job listings to load. We use a generic approach since classes change often
                page.wait_for_timeout(5000)
                
                # Often roles are in elements with "job" in class or data-test
                job_cards = page.query_selector_all("div[class*='job'], div[class*='Job']")
                
                # Fallback if no cards found (anti-bot)
                if not job_cards:
                     print("Wellfound: Could not find job cards, might be blocked by Cloudflare.")
                     
                for card in job_cards[:settings.max_jobs_per_source]:
                    # Extract raw text and try to heuristically split it, or find standard tags
                    text_content = card.inner_text().strip()
                    if not text_content or "Data" not in text_content:
                        continue
                        
                    lines = [line.strip() for line in text_content.split('\n') if line.strip()]
                    if len(lines) < 2:
                        continue
                        
                    title_text = lines[0] # Usually the first line is title or company
                    company_text = lines[1] if len(lines) > 1 else "Unknown"
                    location_text = "Remote"
                    
                    # Try to find a link
                    link_elem = card.query_selector("a")
                    href = link_elem.get_attribute("href") if link_elem else ""
                    full_link = f"https://wellfound.com{href}" if href.startswith("/") else href
                    
                    jobs.append({
                        "job_id": f"wf_{uuid.uuid4().hex[:8]}",
                        "company": self.clean_title(company_text),
                        "title": self.clean_title(title_text),
                        "location": location_text,
                        "remote": True,
                        "internship": "intern" in title_text.lower() or "intern" in text_content.lower(),
                        "experience_required": "Unknown",
                        "salary": None,
                        "skills": None,
                        "posting_date": now,
                        "apply_link": full_link or url, # Fallback to search page if no link
                        "full_job_description": text_content[:5000],
                        "source": "Wellfound",
                        "timestamp": now
                    })
                    
                browser.close()
        except Exception as e:
            print(f"Wellfound Playwright scraper error: {e}")
            
        return jobs
