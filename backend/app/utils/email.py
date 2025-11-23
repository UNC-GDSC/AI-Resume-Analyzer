"""Email notification service."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
from app.core.config import settings
from loguru import logger


class EmailService:
    """Email service for sending notifications."""

    def __init__(self):
        """Initialize email service."""
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.email_from = settings.EMAIL_FROM

    def send_email(
        self, to: str, subject: str, body: str, html: bool = True
    ) -> bool:
        """Send an email.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body
            html: Whether body is HTML

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.smtp_user or not self.smtp_password:
            logger.warning("Email service not configured")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = self.email_from
            msg["To"] = to
            msg["Subject"] = subject

            if html:
                msg.attach(MIMEText(body, "html"))
            else:
                msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {to}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to}: {str(e)}")
            return False

    def send_ranking_complete_notification(
        self, to: str, job_title: str, total_resumes: int, job_id: int
    ) -> bool:
        """Send notification when resume ranking is complete.

        Args:
            to: Recipient email
            job_title: Job title
            total_resumes: Number of resumes processed
            job_id: Job ID

        Returns:
            True if sent successfully
        """
        subject = f"Resume Ranking Complete: {job_title}"
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2563eb;">Resume Ranking Complete</h2>
                    <p>Your resume ranking for <strong>{job_title}</strong> has been completed.</p>
                    <div style="background-color: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <p style="margin: 0;"><strong>Total Resumes Analyzed:</strong> {total_resumes}</p>
                    </div>
                    <p>
                        <a href="http://localhost:3000/jobs/{job_id}"
                           style="display: inline-block; padding: 12px 24px; background-color: #2563eb;
                                  color: white; text-decoration: none; border-radius: 6px; font-weight: bold;">
                            View Rankings
                        </a>
                    </p>
                    <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                        This is an automated message from AI Resume Analyzer.
                    </p>
                </div>
            </body>
        </html>
        """
        return self.send_email(to, subject, body, html=True)

    def send_batch_upload_notification(
        self, to: str, job_title: str, successful: int, failed: int
    ) -> bool:
        """Send notification after batch upload.

        Args:
            to: Recipient email
            job_title: Job title
            successful: Number of successful uploads
            failed: Number of failed uploads

        Returns:
            True if sent successfully
        """
        subject = f"Batch Upload Complete: {job_title}"
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2563eb;">Batch Upload Complete</h2>
                    <p>Your batch resume upload for <strong>{job_title}</strong> has been processed.</p>
                    <div style="background-color: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <p style="margin: 5px 0;"><strong>Successful:</strong> <span style="color: #10b981;">{successful}</span></p>
                        <p style="margin: 5px 0;"><strong>Failed:</strong> <span style="color: #ef4444;">{failed}</span></p>
                    </div>
                    <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                        This is an automated message from AI Resume Analyzer.
                    </p>
                </div>
            </body>
        </html>
        """
        return self.send_email(to, subject, body, html=True)
