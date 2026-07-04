from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime
import os

Base = declarative_base()

class Job(Base):
    __tablename__ = 'jobs'

    job_id = Column(String, primary_key=True, index=True)
    company = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False, index=True)
    location = Column(String, nullable=True)
    remote = Column(Boolean, default=False)
    internship = Column(Boolean, default=False)
    experience_required = Column(String, nullable=True)
    salary = Column(String, nullable=True)
    skills = Column(Text, nullable=True)
    
    posting_date = Column(DateTime, nullable=True)
    application_deadline = Column(DateTime, nullable=True)
    recruiter_name = Column(String, nullable=True)
    company_website = Column(String, nullable=True)
    apply_link = Column(String, nullable=False)
    full_job_description = Column(Text, nullable=True)
    benefits = Column(Text, nullable=True)
    required_technologies = Column(Text, nullable=True)
    education_requirement = Column(String, nullable=True)
    source = Column(String, nullable=False)
    
    # AI Extractions
    summary = Column(Text, nullable=True)
    resume_match_score = Column(Float, nullable=True)
    match_explanation = Column(Text, nullable=True)
    missing_skills = Column(Text, nullable=True)
    resume_improvements = Column(Text, nullable=True)
    resume_summary = Column(Text, nullable=True)
    cover_letter = Column(Text, nullable=True)
    interview_questions = Column(Text, nullable=True)
    recommended_projects = Column(Text, nullable=True)
    
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

# Ensure data directory exists
data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
os.makedirs(data_dir, exist_ok=True)
DATABASE_URL = f"sqlite:///{os.path.join(data_dir, 'jobs.db')}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
