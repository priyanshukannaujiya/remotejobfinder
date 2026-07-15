import pandas as pd
import json
import os
from datetime import datetime
from .models import Job, SessionLocal, data_dir


class DatabaseManager:
    def __init__(self):
        self.csv_path = os.path.join(data_dir, "jobs.csv")
        self.json_path = os.path.join(data_dir, "jobs.json")

    def save_jobs(self, jobs_data: list[dict]):
        """
        Saves a list of job dictionaries to the database, CSV, and JSON.
        Avoids duplicates based on job_id.
        """
        if not jobs_data:
            return 0

        new_jobs_added = 0
        db = SessionLocal()
        try:
            job_ids = [j["job_id"] for j in jobs_data]
            existing_ids = {
                r[0] for r in db.query(Job.job_id).filter(Job.job_id.in_(job_ids)).all()
            }

            valid_keys = {c.name for c in Job.__table__.columns}
            for job_dict in jobs_data:
                if job_dict["job_id"] not in existing_ids:
                    filtered_dict = {k: v for k, v in job_dict.items() if k in valid_keys}
                    db_job = Job(**filtered_dict)
                    db.add(db_job)
                    existing_ids.add(job_dict["job_id"])
                    new_jobs_added += 1
            db.commit()
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

        if new_jobs_added > 0:
            self._update_csv_and_json()

        return new_jobs_added

    def _update_csv_and_json(self):
        """Dump the entire database to CSV and JSON."""
        db = SessionLocal()
        try:
            jobs = db.query(Job).all()

            # Convert to list of dicts
            jobs_list = []
            for j in jobs:
                j_dict = j.__dict__.copy()
                j_dict.pop("_sa_instance_state", None)
                # Convert datetime to string for JSON serialization
                for k, v in j_dict.items():
                    if isinstance(v, datetime):
                        j_dict[k] = v.isoformat()
                jobs_list.append(j_dict)

            # Write JSON
            with open(self.json_path, "w", encoding="utf-8") as f:
                json.dump(jobs_list, f, indent=4, ensure_ascii=False)

            # Write CSV
            if jobs_list:
                df = pd.DataFrame(jobs_list)
                df.to_csv(self.csv_path, index=False)

        finally:
            db.close()

    def get_todays_jobs(self) -> list[dict]:
        """Fetch all jobs scraped today for the daily summary report."""
        db = SessionLocal()
        try:
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            jobs = db.query(Job).filter(Job.timestamp >= today).all()

            jobs_list = []
            for j in jobs:
                j_dict = j.__dict__.copy()
                j_dict.pop("_sa_instance_state", None)
                jobs_list.append(j_dict)
            return jobs_list
        finally:
            db.close()

    def filter_new_jobs(self, jobs_data: list[dict]) -> list[dict]:
        """Filters a list of jobs, returning only those not yet in the database."""
        if not jobs_data:
            return []

        db = SessionLocal()
        new_jobs = []
        try:
            job_ids = [j["job_id"] for j in jobs_data]
            existing_ids = {
                r[0] for r in db.query(Job.job_id).filter(Job.job_id.in_(job_ids)).all()
            }

            for job in jobs_data:
                if job["job_id"] not in existing_ids:
                    new_jobs.append(job)
            return new_jobs
        finally:
            db.close()

    def job_exists(self, job_id: str) -> bool:
        """Check if a single job_id already exists in the database."""
        db = SessionLocal()
        try:
            return db.query(Job.job_id).filter(Job.job_id == job_id).first() is not None
        finally:
            db.close()


db_manager = DatabaseManager()
