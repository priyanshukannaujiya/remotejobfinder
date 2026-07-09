import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import List, Dict
import os
import json
from ..config.settings import settings
from ..database.models import data_dir
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class EmailSender:
    def __init__(self):
        self.email = settings.email
        self.password = settings.app_password
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 465

    def generate_html_report(self, jobs: List[Dict], news: List[Dict] = None) -> str:
        if not jobs:
            return "<h2>No new jobs found today.</h2>"

        total_jobs = len(jobs)
        remote_jobs = sum(1 for j in jobs if j.get("remote"))
        internships = sum(1 for j in jobs if j.get("internship"))

        # Sort by match score
        top_jobs = sorted(
            jobs, key=lambda x: x.get("resume_match_score", 0) or 0, reverse=True
        )[:10]

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
        """

        if news:
            html += """
            <div class="summary-box">
                <h3>🔥 Latest Data Engineering Trends</h3>
                <ul style="list-style-type: none; padding-left: 0;">
            """
            for item in news:
                html += f"""
                    <li style="margin-bottom: 10px;">
                        <a href="{item.get('url')}" style="font-size: 16px; font-weight: bold; color: #0056b3; text-decoration: none;">{item.get('title')}</a>
                        <p style="margin: 5px 0 0 0; color: #555;">{item.get('description')}</p>
                    </li>
                """
            html += """
                </ul>
            </div>
            """

        html += """
            <h3>Top 10 Matches</h3>
        """

        for job in top_jobs:
            score = job.get("resume_match_score", "N/A")
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

    def send_report(self, jobs: List[Dict], news: List[Dict] = None):
        if not jobs:
            logger.info("No jobs to email.")
            return

        recipients = [
            self.email,
            "atharvbhosale03@gmail.com",
            "kannaujiyapriyanshu111@gmail.com",
            "aaditya.2007singh@gmail.com",
            "bhosaleatharv16@gmail.com",
            "bhosaleatharv03@gmail.com",
        ]

        # Add subscribers from json file
        subscribers_file = os.path.join(data_dir, "subscribers.json")
        if os.path.exists(subscribers_file):
            try:
                with open(subscribers_file, "r") as f:
                    subscribers = json.load(f)
                    recipients.extend(subscribers)
            except Exception as e:
                logger.error(f"Failed to read subscribers file: {e}")

        # Remove duplicates while preserving order
        recipients = list(dict.fromkeys(recipients))

        msg = MIMEMultipart()
        msg["From"] = self.email
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = f"Daily Data Engineering Jobs Report - {len(jobs)} New Jobs"

        html_content = self.generate_html_report(jobs, news=news)
        msg.attach(MIMEText(html_content, "html"))

        # Attach CSV
        csv_path = os.path.join(data_dir, "jobs.csv")
        if os.path.exists(csv_path):
            with open(csv_path, "rb") as f:
                part = MIMEApplication(f.read(), Name="jobs.csv")
                part["Content-Disposition"] = 'attachment; filename="jobs.csv"'
                msg.attach(part)

        import time
        import ssl
        max_retries = 3
        for attempt in range(max_retries):
            try:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context, timeout=15)
                server.login(self.email, self.password)
                server.send_message(msg)
                server.quit()
                logger.info("Email report sent successfully!")
                break
            except Exception as e:
                logger.error(f"Failed to send email (attempt {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    logger.info("Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    logger.error("Max retries reached. Email sending failed permanently.")

    def send_dream_job_alert(self, job: Dict):
        recipient = "kannaujiyapriyanshu111@gmail.com"

        msg = MIMEMultipart()
        msg["From"] = self.email
        msg["To"] = recipient
        msg["Subject"] = (
            f"🚨 URGENT: Dream Job Alert! {job.get('title')} @ {job.get('company')}"
        )

        score = job.get("resume_match_score", "N/A")
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

        msg.attach(MIMEText(html, "html"))

        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=15)
                server.login(self.email, self.password)
                server.send_message(msg)
                server.quit()
                logger.info(f"Dream job alert sent to {recipient}!")
                break
            except Exception as e:
                logger.error(f"Failed to send dream job alert (attempt {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    logger.info("Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    logger.error("Max retries reached. Dream job alert failed permanently.")

    def send_welcome_email(self, recipient: str):
        msg = MIMEMultipart()
        msg["From"] = self.email
        msg["To"] = recipient
        msg["Subject"] = "Welcome to Data Engineering Job Hunter! 🚀"

        html = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .welcome-box { background-color: #e9ecef; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
            </style>
        </head>
        <body>
            <div class="welcome-box">
                <h2>Welcome to Data Engineering Job Hunter! 🚀</h2>
                <p>Hi there,</p>
                <p>Thank you for subscribing to our daily job alerts.</p>
                <p>You will now receive a comprehensive summary of the latest Data Engineering jobs, including remote opportunities and internships, <strong>every day at 10:00 AM IST</strong>.</p>
                <p>We analyze thousands of jobs and use AI to match them against the ideal criteria, helping you find the perfect fit faster.</p>
                <br>
                <p>Best regards,<br>Data Engineering Job Hunter Team</p>
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(html, "html"))

        try:
            server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=10)
            server.login(self.email, self.password)
            server.send_message(msg)
            server.quit()
            logger.info(f"Welcome email sent successfully to {recipient}!")
        except Exception as e:
            logger.error(f"Failed to send welcome email to {recipient}: {e}")

    def send_failure_alert(self, error_details: str):
        msg = MIMEMultipart()
        msg["From"] = self.email
        msg["To"] = f"{self.email}, kannaujiyapriyanshu111@gmail.com"
        msg["Subject"] = "🚨 SYSTEM FAILURE: Job Scraper Pipeline Crashed"

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .alert-box {{ background-color: #ffcccb; padding: 15px; border-radius: 5px; margin-bottom: 20px; border: 2px solid red; }}
            </style>
        </head>
        <body>
            <div class="alert-box">
                <h2 style="color: red; margin-top: 0;">🚨 CRITICAL ERROR!</h2>
                <p>The job scraper script encountered a fatal error and stopped running.</p>
                <h3>Error Details:</h3>
                <pre style="background: #f4f4f4; padding: 10px; border: 1px solid #ddd; overflow-x: auto;">{error_details}</pre>
                <p>Please check the GitHub Actions logs for more information.</p>
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(html, "html"))
        
        try:
            server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=10)
            server.login(self.email, self.password)
            server.send_message(msg)
            server.quit()
            logger.info("Failure email sent successfully!")
        except Exception as e:
            logger.error(f"Failed to send failure email: {e}")


