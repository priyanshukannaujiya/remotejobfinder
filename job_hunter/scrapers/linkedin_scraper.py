import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from datetime import datetime
import uuid
import time
from .base import BaseScraper
from ..config.settings import settings

class LinkedInScraper(BaseScraper):
    """
    Scrapes LinkedIn public job postings.
    Uses basic requests to avoid login walls for public listings.
    """
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.linkedin.com/jobs/search"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
        }
        # Searching for Data Engineer in India and Worldwide Remote
        # f_TPR=r86400 ensures we ONLY get jobs posted in the Past 24 Hours
        self.search_urls = [
            f"{self.base_url}?keywords=Data%20Engineer&location=India&f_WT=2&f_TPR=r86400", # Remote India (Past 24h)
            f"{self.base_url}?keywords=Data%20Engineer&location=India&f_E=1,2&f_TPR=r86400", # Intern/Entry Level India (Past 24h)
        ]

    def fetch_jobs(self) -> List[Dict]:
        jobs = []
        now = datetime.utcnow()
        
        for url in self.search_urls:
            try:
                print(f"Fetching URL: {url}")
                response = requests.get(url, headers=self.headers, timeout=10)
                print(f"Got response: {response.status_code}")
                if response.status_code != 200:
                    print(f"LinkedIn scraper failed with status code {response.status_code}")
                    continue
                    
                soup = BeautifulSoup(response.text, 'html.parser')
                job_cards = soup.find_all('div', class_='base-card')
                
                for card in job_cards:
                    if len(jobs) >= settings.max_jobs_per_source:
                        break
                        
                    title_elem = card.find('h3', class_='base-search-card__title')
                    company_elem = card.find('h4', class_='base-search-card__subtitle')
                    location_elem = card.find('span', class_='job-search-card__location')
                    link_elem = card.find('a', class_='base-card__full-link')
                    
                    if not title_elem or not link_elem:
                        continue
                        
                    title_text = title_elem.text.strip()
                    company_text = company_elem.text.strip() if company_elem else "Unknown Company"
                    location_text = location_elem.text.strip() if location_elem else "Unknown Location"
                    apply_link = link_elem.get('href', '').split('?')[0] # keep base link without tracking
                    
                    # Fetch full job description
                    full_desc_text = f"{title_text} at {company_text} in {location_text}"
                    try:
                        time.sleep(1) # Be polite when hitting individual job pages
                        job_res = requests.get(apply_link, headers=self.headers, timeout=10)
                        if job_res.status_code == 200:
                            job_soup = BeautifulSoup(job_res.text, 'html.parser')
                            desc_elem = job_soup.find('div', class_='show-more-less-html__markup')
                            if desc_elem:
                                full_desc_text = desc_elem.text.strip()
                    except Exception as desc_e:
                        print(f"Failed to fetch description for {apply_link}: {desc_e}")
                    
                    jobs.append({
                        "job_id": self.generate_job_id("li", company_text, title_text),
                        "company": self.clean_title(company_text),
                        "title": self.clean_title(title_text),
                        "location": location_text,
                        "remote": "remote" in location_text.lower() or "remote" in title_text.lower(),
                        "internship": "intern" in title_text.lower(),
                        "experience_required": "Unknown",
                        "salary": None,
                        "skills": None,
                        "posting_date": now,
                        "apply_link": apply_link,
                        "full_job_description": full_desc_text,
                        "source": "LinkedIn",
                        "timestamp": now
                    })
                    
                time.sleep(2) # Politeness delay between searches
            except Exception as e:
                print(f"Error in LinkedIn Scraper: {e}")
                
        return jobs
