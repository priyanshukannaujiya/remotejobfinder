import json
from typing import Dict, List
import google.generativeai as genai
from ..config.settings import settings

class LLMProcessor:
    def __init__(self):
        self.api_key = settings.gemini_api_key
        if self.api_key:
            genai.configure(api_key=self.api_key)
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
            "You will be given a job description and the candidate's resume summary. "
            "Return a JSON object with exactly these fields:\n"
            "- summary: A string with exactly 3 bullet points summarizing the job.\n"
            "- resume_match_score: An integer from 0 to 100 representing how well the candidate fits.\n"
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
