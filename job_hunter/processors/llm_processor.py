import json
from typing import Dict, List
import google.generativeai as genai
from ..config.settings import settings

class LLMProcessor:
    def __init__(self):
        self.api_keys = settings.get_gemini_api_keys_list
        self.current_key_idx = 0
        if self.api_keys:
            genai.configure(api_key=self.api_keys[0])
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            self.model = None
        
        self.dummy_resume = """
        I am a fresh Data Engineering graduate. I have strong skills in Python, SQL, and Pandas.
        I have completed academic projects using Apache Spark and PostgreSQL. 
        I am looking for an entry-level or junior remote data engineering role.
        """
        
    def process_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """
        Takes a list of jobs, calls OpenAI for each to get a summary and score,
        and returns the enriched job list.
        """
        if not self.model:
            print("No Gemini API Key found. Skipping LLM processing.")
            return jobs
            
        enriched_jobs = []
        for job in jobs:
            if self.api_keys:
                self.current_key_idx = (self.current_key_idx + 1) % len(self.api_keys)
                genai.configure(api_key=self.api_keys[self.current_key_idx])
                
            try:
                result = self._analyze_job(job)
                job.update(result)
            except Exception as e:
                print(f"Error processing job {job.get('job_id')}: {e}")
            enriched_jobs.append(job)
            
        return enriched_jobs
        
    def _analyze_job(self, job: Dict) -> Dict:
        system_prompt = (
            "You are an AI assistant helping a data engineer find a job. "
            "You must STRICTLY evaluate the job against these criteria:\n"
            "1. MUST NOT require more than 2 years of experience. If it requires 3+ years, set resume_match_score to 0.\n"
            "2. Location preference: Remote (Worldwide) OR physically in India. Prioritize Remote Internship, Data Engineering Internship, or Fresher roles.\n"
            "3. The job should match common Data Engineering keywords (e.g. Data Engineer, ETL Developer, Big Data, Snowflake, Spark, Python SQL).\n"
            "Return a JSON object with exactly these fields:\n"
            "- summary: A list of 3 string bullet points summarizing the job.\n"
            "- resume_match_score: An integer from 0 to 100 representing how well the candidate fits (0 if senior/requires >2 yrs).\n"
            "- match_explanation: A short string explaining the score."
        )
        
        user_prompt = f"Candidate Resume:\n{self.dummy_resume}\n\nJob Info:\nTitle: {job.get('title')}\nDescription: {job.get('full_job_description')}\n\nProvide the output in JSON format."
        
        response = self.model.generate_content(
            system_prompt + "\n\n" + user_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                response_mime_type="application/json",
            ),
        )
        
        content = response.text
        data = json.loads(content)
        if isinstance(data.get('summary'), list):
            data['summary'] = '\n'.join(f"- {item}" for item in data['summary'])
        return data
