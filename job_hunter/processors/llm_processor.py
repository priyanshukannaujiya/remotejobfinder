import json
from typing import Dict, List
import google.generativeai as genai
from openai import OpenAI
from ..config.settings import settings
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class LLMProcessor:
    def __init__(self):
        self.api_keys = settings.get_gemini_api_keys_list
        self.current_key_idx = 0
        self.gemini_model = None
        self.openai_client = None

        self.model_name = None
        
        if settings.groq_api_key:
            self.openai_client = OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=settings.groq_api_key,
            )
            self.model_name = "llama3-70b-8192"
        elif settings.openrouter_api_key:
            self.openai_client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=settings.openrouter_api_key,
            )
            self.model_name = "google/gemini-2.5-flash"
        elif self.api_keys:
            genai.configure(api_key=self.api_keys[0])
            self.gemini_model = genai.GenerativeModel("gemini-2.5-flash")

        self.dummy_resume = """
        You are an expert technical recruiter and Data Engineering hiring manager.

        I am a final-year B.E. student specializing in Artificial Intelligence and Machine Learning, actively seeking an entry-level or junior Data Engineering role (remote, hybrid, or onsite).

        My primary skills include:

        Programming:
        - Python
        - SQL
        - PySpark
        - Pandas
        - NumPy

        Data Engineering:
        - ETL/ELT Pipeline Development
        - Data Warehousing
        - Data Modeling
        - Medallion Architecture (Bronze, Silver, Gold)
        - Batch Data Processing
        - Data Cleaning & Transformation
        - Metadata-Driven Pipelines
        - Workflow Automation

        Cloud Platforms:
        - Microsoft Azure
            - Azure Data Factory (ADF)
            - Azure Data Lake Storage Gen2 (ADLS Gen2)
            - Azure Databricks
            - Azure Synapse Analytics
            - Azure SQL Database
            - Azure Blob Storage
            - Azure Key Vault
            - Self-Hosted Integration Runtime

        Databases:
        - Microsoft SQL Server
        - PostgreSQL
        - MySQL
        - Snowflake

        Big Data Technologies:
        - Apache Spark
        - PySpark
        - Hadoop (HDFS)
        - Apache Hive
        - Apache Kafka (Basics)

        Data Transformation:
        - Databricks Notebooks
        - Spark SQL
        - SQL Stored Procedures
        - Python ETL Scripts

        Business Intelligence:
        - Microsoft Power BI
        - Tableau

        Version Control & DevOps:
        - Git
        - GitHub
        - GitHub Actions (Basics)

        Containerization & Deployment:
        - Docker (Basics)

        Operating Systems:
        - Linux
        - Windows

        Development Tools:
        - Visual Studio Code
        - Jupyter Notebook
        - Azure Portal
        - SQL Server Management Studio (SSMS)
        - pgAdmin

        Libraries:
        - Pandas
        - NumPy
        - Requests
        - SQLAlchemy
        - PyODBC
        - OpenPyXL

        Concepts:
        - Data Pipelines
        - Data Lakes
        - Data Warehouses
        - Incremental Loading
        - Full Load Processing
        - Change Data Capture (CDC)
        - Partitioning
        - Data Validation
        - Data Quality
        - Performance Optimization
        - Star Schema
        - Snowflake Schema
        - Slowly Changing Dimensions (SCD)
        - Data Governance (Basics)

        Projects:
        - Azure Medallion Data Engineering Pipeline
        - Snowflake Cloud Data Warehouse Project
        - Cloud Cost Monitoring & Analytics Platform
        - Amazon Retail Data Pipeline
        - End-to-End ETL Pipelines using Azure and Databricks

        Career Objective:
        I am looking for an entry-level or junior Data Engineering position where I can build scalable data pipelines, optimize ETL workflows, work with cloud platforms, and contribute to modern data engineering solutions.

        Whenever I provide a job description:
        1. Analyze the job requirements.
        2. Compare them with my skills.
        3. Calculate a skill match percentage.
        4. Identify missing skills.
        5. Suggest improvements for my resume.
        6. Generate an ATS-optimized resume summary.
        7. Write a customized cover letter.
        8. Suggest interview questions based on the job.
        9. Recommend projects to bridge any skill gaps.
        """

    def process_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """
        Takes a list of jobs, calls OpenAI for each to get a summary and score,
        and returns the enriched job list.
        """
        if not self.gemini_model and not self.openai_client:
            logger.warning(
                "No Gemini or OpenRouter API Key found. Skipping LLM processing."
            )
            return jobs

        enriched_jobs = []
        for job in jobs:
            import time
            
            max_retries = (len(self.api_keys) * 2) if self.api_keys else 3
            for attempt in range(max_retries):
                try:
                    time.sleep(5)  # Prevent spamming the API and stay well within limits
                    result = self._analyze_job(job)
                    job.update(result)
                    break
                except Exception as e:
                    error_str = str(e)
                    if "429" in error_str:
                        if not self.openai_client and self.api_keys:
                            self.current_key_idx = (self.current_key_idx + 1) % len(self.api_keys)
                            genai.configure(api_key=self.api_keys[self.current_key_idx])
                            logger.warning(f"Rate limit (429) hit. Switched to API key {self.current_key_idx + 1}/{len(self.api_keys)}")
                        
                        # Only sleep if we've cycled through all keys
                        if attempt > 0 and attempt % len(self.api_keys) == 0:
                            logger.warning(f"All keys rate limited for job {job.get('job_id')}. Sleeping 60s... (Attempt {attempt+1}/{max_retries})")
                            time.sleep(60)
                    else:
                        logger.error(f"Error processing job {job.get('job_id')}: {e}")
                        break
            enriched_jobs.append(job)

        return enriched_jobs

    def _analyze_job(self, job: Dict) -> Dict:
        system_prompt = (
            "You are an AI assistant helping a data engineer find a job. "
            "You must STRICTLY evaluate the job against these criteria:\n"
            "1. MUST NOT require more than 2 years of experience. If it requires 3+ years, set resume_match_score to 0.\n"
            "2. Location preferences:\n"
            "   - FIRST Priority: Mumbai, Pune.\n"
            "   - SECOND Priority: Remote (Worldwide or India).\n"
            "   - LAST Priority: Bangalore / Bengaluru.\n"
            "   - STRICTLY IGNORE: Jobs in North India (e.g., Delhi, Noida, Gurgaon). Set resume_match_score to 0 for these.\n"
            "3. The job should match common Data Engineering keywords (e.g. Data Engineer, ETL Developer, Big Data, Snowflake, Spark, Python SQL).\n"
            "Return a JSON object with exactly these fields:\n"
            "- experience_required: A short string indicating the years of experience required (e.g. '0-1 years', 'Fresher', '3+ years').\n"
            "- skills: A comma-separated string of required technical skills.\n"
            "- summary: A list of 3 string bullet points summarizing the job requirements.\n"
            "- resume_match_score: An integer from 0 to 100 representing how well the candidate fits (0 if senior/requires >2 yrs).\n"
            "- match_explanation: A short string explaining the score and comparing skills.\n"
            "- missing_skills: A list of strings identifying missing skills.\n"
            "- resume_improvements: A string suggesting resume improvements.\n"
            "- resume_summary: A string containing an ATS-optimized resume summary.\n"
            "- cover_letter: A string containing a customized cover letter.\n"
            "- interview_questions: A list of strings with suggested interview questions.\n"
            "- recommended_projects: A list of strings recommending projects to bridge gaps."
        )

        user_prompt = f"Candidate Resume:\n{self.dummy_resume}\n\nJob Info:\nTitle: {job.get('title')}\nDescription: {job.get('full_job_description')}\n\nProvide the output in JSON format."

        if self.openai_client:
            response = self.openai_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
        else:
            response = self.gemini_model.generate_content(
                system_prompt + "\n\n" + user_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    response_mime_type="application/json",
                ),
            )

        content = response.text if not self.openai_client else content

        # Robust JSON parsing
        try:
            # Sometime LLMs wrap json in markdown blocks like ```json ... ```
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            data = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to parse JSON from LLM: {e}. Raw content: {content[:200]}..."
            )
            data = {
                "summary": "Failed to extract summary.",
                "resume_match_score": 0,
                "match_explanation": "Failed to parse LLM response.",
                "missing_skills": [],
                "resume_improvements": "",
                "resume_summary": "",
                "cover_letter": "",
                "interview_questions": [],
                "recommended_projects": [],
                "experience_required": "Unknown",
                "skills": "Unknown",
            }

        for field in [
            "summary",
            "missing_skills",
            "interview_questions",
            "recommended_projects",
        ]:
            if isinstance(data.get(field), list):
                data[field] = "\n".join(f"- {item}" for item in data[field])
        return data
