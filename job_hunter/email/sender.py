import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import List, Dict
import os
from ..config.settings import settings
from ..database.models import data_dir
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

class EmailSender:
    def __init__(self):
        self.email = settings.email
        self.password = settings.app_password
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        
    def generate_html_report(self, jobs: List[Dict]) -> str:
        if not jobs:
            return "<h2>No new jobs found today.</h2>"
            
        total_jobs = len(jobs)
        remote_jobs = sum(1 for j in jobs if j.get('remote'))
        internships = sum(1 for j in jobs if j.get('internship'))
        
        # Sort by match score
        top_jobs = sorted(jobs, key=lambda x: x.get('resume_match_score', 0) or 0, reverse=True)[:10]
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .summary-box {{ background-color: #f4f4f4; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .job-card {{ border: 1px solid #ddd; padding: 15px; margin-bottom: 15px; border-radius: 5px; }}
                .job-title {{ font-size: 18px; color: #0056b3; margin-top: 0; }}
                .company {{ font-weight: bold; }}
                .score {{ color: #28a745; font-weight: bold; }}
                .apply-btn {{ display: inline-block; padding: 10px 15px; background-color: #007bff; color: white; text-decoration: none; border-radius: 3px; margin-top: 10px; }}
            </style>
        </head>
        <body>
            <h2>Daily Data Engineering Jobs Report</h2>
            
            <div class="summary-box">
                <h3>Summary</h3>
                <ul>
                    <li>Total Jobs Found: {total_jobs}</li>
                    <li>Remote Jobs: {remote_jobs}</li>
                    <li>Internships: {internships}</li>
                </ul>
            </div>
            
            <h3>Top 10 Matches</h3>
        """
        
        for job in top_jobs:
            score = job.get('resume_match_score', 'N/A')
            html += f"""
            <div class="job-card">
                <h4 class="job-title">{job.get('title')} @ <span class="company">{job.get('company')}</span></h4>
                <p><strong>Location:</strong> {job.get('location')} | <strong>Experience:</strong> {job.get('experience_required')}</p>
                <p><strong>Skills:</strong> {job.get('skills')}</p>
                <p><strong>Match Score:</strong> <span class="score">{score}/100</span> - {job.get('match_explanation')}</p>
                <p><strong>Summary:</strong><br>{job.get('summary')}</p>
                <a href="{job.get('apply_link')}" class="apply-btn">Apply Now</a>
            </div>
            """
            
        html += """
        </body>
        </html>
        """
        return html
        
    def send_report(self, jobs: List[Dict]):
        if not jobs:
            logger.info("No jobs to email.")
            return
            
        recipients = [
            self.email,
            "atharvbhosale03@gmail.com",
            "kannaujiyapriyanshu111@gmail.com",
            "aaditya.2007singh@gmail.com",
            "bhosaleatharv16@gmail.com",
            "bhosaleatharv03@gmail.com"
        ]
        
        msg = MIMEMultipart()
        msg['From'] = self.email
        msg['To'] = ", ".join(recipients)
        msg['Subject'] = f"Daily Data Engineering Jobs Report - {len(jobs)} New Jobs"
        
        html_content = self.generate_html_report(jobs)
        msg.attach(MIMEText(html_content, 'html'))
        
        # Attach CSV
        csv_path = os.path.join(data_dir, 'jobs.csv')
        if os.path.exists(csv_path):
            with open(csv_path, 'rb') as f:
                part = MIMEApplication(f.read(), Name='jobs.csv')
                part['Content-Disposition'] = 'attachment; filename="jobs.csv"'
                msg.attach(part)
                
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email, self.password)
            server.send_message(msg)
            server.quit()
            logger.info("Email report sent successfully!")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")

    def send_dream_job_alert(self, job: Dict):
        recipient = "kannaujiyapriyanshu111@gmail.com"
        
        msg = MIMEMultipart()
        msg['From'] = self.email
        msg['To'] = recipient
        msg['Subject'] = f"🚨 URGENT: Dream Job Alert! {job.get('title')} @ {job.get('company')}"
        
        score = job.get('resume_match_score', 'N/A')
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .alert-box {{ background-color: #ffcccb; padding: 15px; border-radius: 5px; margin-bottom: 20px; border: 2px solid red; }}
                .job-card {{ border: 1px solid #ddd; padding: 15px; border-radius: 5px; }}
                .job-title {{ font-size: 18px; color: #0056b3; margin-top: 0; }}
                .company {{ font-weight: bold; }}
                .score {{ color: #28a745; font-weight: bold; }}
                .apply-btn {{ display: inline-block; padding: 10px 15px; background-color: #007bff; color: white; text-decoration: none; border-radius: 3px; margin-top: 10px; }}
            </style>
        </head>
        <body>
            <div class="alert-box">
                <h2 style="color: red; margin-top: 0;">🚨 PERFECT MATCH FOUND!</h2>
                <p>This job meets your criteria: High Match Score, Fresher/0-1 Year Experience, and target location (Mumbai/Pune/Remote).</p>
            </div>
            
            <div class="job-card">
                <h3 class="job-title">{job.get('title')} @ <span class="company">{job.get('company')}</span></h3>
                <p><strong>Location:</strong> {job.get('location')} | <strong>Experience:</strong> {job.get('experience_required')}</p>
                <p><strong>Skills:</strong> {job.get('skills')}</p>
                <p><strong>Match Score:</strong> <span class="score">{score}/100</span> - {job.get('match_explanation')}</p>
                <p><strong>Summary:</strong><br>{job.get('summary')}</p>
                <a href="{job.get('apply_link')}" class="apply-btn">Apply Now</a>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html, 'html'))
        
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email, self.password)
            server.send_message(msg)
            server.quit()
            logger.info(f"Dream job alert sent to {recipient}!")
        except Exception as e:
            logger.error(f"Failed to send dream job alert: {e}")
