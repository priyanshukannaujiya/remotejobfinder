from typing import List, Dict
import pandas as pd

class DataCleaner:
    @staticmethod
    def clean_jobs(jobs: List[Dict]) -> List[Dict]:
        """
        Cleans a list of job dictionaries:
        - Removes tracking parameters from URLs.
        - Normalizes company names.
        - Converts missing values to None.
        - Removes explicit duplicates based on company and title.
        """
        if not jobs:
            return []
            
        df = pd.DataFrame(jobs)
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['company', 'title'], keep='first')
        
        # Normalize company names (uppercase, strip)
        if 'company' in df.columns:
            df['company'] = df['company'].astype(str).str.strip().str.title()
            
        # Clean URLs (remove tracking parameters but keep IDs)
        if 'apply_link' in df.columns:
            def clean_url(url):
                if not isinstance(url, str): return url
                # Remove common tracking patterns if present
                if '?utm_' in url:
                    url = url.split('?utm_')[0]
                if '&utm_' in url:
                    url = url.split('&utm_')[0]
                return url
            df['apply_link'] = df['apply_link'].apply(clean_url)
            
        # Convert NaN to None for database compatibility
        df = df.where(pd.notnull(df), None)
        
        return df.to_dict('records')
