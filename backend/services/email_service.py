"""
Email Service
Handles sending email notifications for critical safety events
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, List
from datetime import datetime

from utils.config import settings

logger = logging.getLogger("chatbot.email_service")


class EmailService:
    """
    Email Service - sends email notifications for critical safety events

    Features:
    - SMTP email sending with TLS support
    - HTML and plain text email support
    - Email template formatting
    - Connection pooling and error handling
    - Configurable SMTP settings from environment

    Usage:
        email_service.send_email(
            to_email="parent@example.com",
            subject="Safety Alert",
            body="Alert message",
            html_body="<h1>Alert</h1>"
        )
    """

    def __init__(self):
        """Initialize EmailService"""
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_from_email = settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME
        self.smtp_use_tls = settings.SMTP_USE_TLS
        self.enabled = settings.ENABLE_PARENT_NOTIFICATIONS

        logger.info(
            f"EmailService initialized - Enabled: {self.enabled}, "
            f"SMTP: {self.smtp_host}:{self.smtp_port}"
        )

    def is_configured(self) -> bool:
        """
        Check if email service is properly configured

        Returns:
            True if all required settings are present
        """
        return all([
            self.smtp_host,
            self.smtp_port,
            self.smtp_username,
            self.smtp_password,
            self.smtp_from_email
        ])

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> Dict:
        """
        Send an email notification

        Args:
            to_email: Recipient email address
            subject: Email subject line
            body: Plain text email body
            html_body: Optional HTML email body

        Returns:
            Dictionary with send result
        """
        # Check if email notifications are enabled
        if not self.enabled:
            logger.info(
                f"Email notifications disabled - Would send to {to_email}: {subject}"
            )
            return {
                "success": False,
                "error": "Email notifications are disabled",
                "sent": False
            }

        # Check if email is configured
        if not self.is_configured():
            logger.error("Email service not properly configured")
            return {
                "success": False,
                "error": "Email service not configured",
                "sent": False
            }

        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.smtp_from_email
            message["To"] = to_email
            message["Date"] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")

            # Attach plain text body
            text_part = MIMEText(body, "plain")
            message.attach(text_part)

            # Attach HTML body if provided
            if html_body:
                html_part = MIMEText(html_body, "html")
                message.attach(html_part)

            # Connect to SMTP server and send
            logger.info(f"Connecting to SMTP server {self.smtp_host}:{self.smtp_port}")

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()
                    logger.debug("TLS started")

                # Login
                server.login(self.smtp_username, self.smtp_password)
                logger.debug("SMTP login successful")

                # Send email
                server.send_message(message)
                logger.info(f"Email sent successfully to {to_email}")

            return {
                "success": True,
                "sent": True,
                "to_email": to_email,
                "subject": subject,
                "timestamp": datetime.now().isoformat()
            }

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            return {
                "success": False,
                "error": "SMTP authentication failed",
                "sent": False,
                "details": str(e)
            }

        except smtplib.SMTPException as e:
            logger.error(f"SMTP error while sending email: {e}")
            return {
                "success": False,
                "error": "SMTP error",
                "sent": False,
                "details": str(e)
            }

        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}", exc_info=True)
            return {
                "success": False,
                "error": "Unexpected error",
                "sent": False,
                "details": str(e)
            }

    def send_critical_safety_alert(
        self,
        to_email: str,
        user_name: str,
        category: str,
        severity: str,
        details: Dict,
        timestamp: datetime,
        content_snippet: Optional[str] = None
    ) -> Dict:
        """
        Send a critical safety alert email to parent

        Args:
            to_email: Parent's email address
            user_name: Child's name
            category: Safety category (crisis_suicide, abuse_physical, etc.)
            severity: Severity level
            details: Safety event details
            timestamp: Event timestamp
            content_snippet: Optional snippet of flagged content

        Returns:
            Dictionary with send result
        """
        # Generate email subject and body
        subject = self._generate_alert_subject(category, severity, user_name)
        plain_body = self._generate_plain_text_alert(
            user_name, category, severity, details, timestamp, content_snippet
        )
        html_body = self._generate_html_alert(
            user_name, category, severity, details, timestamp, content_snippet
        )

        return self.send_email(
            to_email=to_email,
            subject=subject,
            body=plain_body,
            html_body=html_body
        )

    def send_bulk_safety_summary(
        self,
        to_email: str,
        user_name: str,
        flags: List[Dict],
        summary_period: str = "daily"
    ) -> Dict:
        """
        Send a bulk summary of safety events

        Args:
            to_email: Parent's email address
            user_name: Child's name
            flags: List of safety flag dictionaries
            summary_period: Summary period (daily, weekly)

        Returns:
            Dictionary with send result
        """
        subject = f"Safety Summary for {user_name} - {summary_period.title()}"

        plain_body = self._generate_plain_text_summary(user_name, flags, summary_period)
        html_body = self._generate_html_summary(user_name, flags, summary_period)

        return self.send_email(
            to_email=to_email,
            subject=subject,
            body=plain_body,
            html_body=html_body
        )

    def _generate_alert_subject(self, category: str, severity: str, user_name: str) -> str:
        """Generate email subject for safety alert"""
        category_subjects = {
            "crisis_suicide": "🚨 URGENT: Suicide-Related Content Detected",
            "crisis_self_harm": "🚨 URGENT: Self-Harm Content Detected",
            "abuse_physical": "🚨 URGENT: Physical Abuse Reported",
            "abuse_emotional": "🚨 URGENT: Emotional Abuse Reported",
            "abuse_sexual": "🚨 URGENT: Sexual Abuse Reported",
            "crisis_general": "🚨 URGENT: Crisis Content Detected",
            "inappropriate_content": "⚠️ High-Severity Content Alert",
            "severe_language": "⚠️ Severe Language Alert",
        }

        default_subject = f"⚠️ Safety Alert for {user_name}"
        return category_subjects.get(category, default_subject)

    def _generate_plain_text_alert(
        self,
        user_name: str,
        category: str,
        severity: str,
        details: Dict,
        timestamp: datetime,
        content_snippet: Optional[str] = None
    ) -> str:
        """Generate plain text email body for safety alert"""
        category_messages = {
            "crisis_suicide": {
                "message": f"{user_name} expressed content related to suicidal thoughts in their conversation.",
                "action": "Please talk to your child immediately and consider contacting a mental health professional.\n\nCrisis Resources:\n- National Suicide Prevention Lifeline: 988\n- Crisis Text Line: Text HOME to 741741"
            },
            "crisis_self_harm": {
                "message": f"{user_name} expressed content related to self-harm in their conversation.",
                "action": "Please talk to your child immediately and consider contacting a mental health professional.\n\nCrisis Resources:\n- Crisis Text Line: Text HOME to 741741"
            },
            "abuse_physical": {
                "message": f"{user_name} described what may be physical abuse in their conversation.",
                "action": "Please speak with your child immediately.\n\nIf you suspect abuse:\n- Childhelp National Child Abuse Hotline: 1-800-422-4453\n- Call 911 if in immediate danger"
            },
            "abuse_emotional": {
                "message": f"{user_name} described what may be emotional abuse in their conversation.",
                "action": "Please speak with your child immediately.\n\nIf you suspect abuse:\n- Childhelp National Child Abuse Hotline: 1-800-422-4453"
            },
            "abuse_sexual": {
                "message": f"{user_name} described what may be sexual abuse in their conversation.",
                "action": "Please speak with your child immediately.\n\nIf you suspect abuse:\n- Childhelp: 1-800-422-4453\n- RAINN: 1-800-656-4673\n- Call 911 if in immediate danger"
            },
        }

        template = category_messages.get(category, {
            "message": f"Safety concern detected in {user_name}'s conversation.",
            "action": "Please review the conversation with your child."
        })

        body = f"""SAFETY ALERT - REQUIRES IMMEDIATE ATTENTION

Time: {timestamp.strftime('%Y-%m-%d %I:%M %p')}
Severity: {severity.upper()}
Child: {user_name}

{template['message']}

RECOMMENDED ACTION:
{template['action']}

---
This notification was generated automatically by the safety monitoring system.
You can review the full conversation details in the parent dashboard.

To disable these notifications, adjust your settings in the parent dashboard.
"""
        return body

    def _generate_html_alert(
        self,
        user_name: str,
        category: str,
        severity: str,
        details: Dict,
        timestamp: datetime,
        content_snippet: Optional[str] = None
    ) -> str:
        """Generate HTML email body for safety alert"""
        severity_colors = {
            "critical": "#dc2626",
            "high": "#ea580c",
            "medium": "#d97706",
            "low": "#ca8a04"
        }

        color = severity_colors.get(severity.lower(), "#6b7280")

        category_messages = {
            "crisis_suicide": {
                "title": "URGENT: Suicide-Related Content Detected",
                "message": f"{user_name} expressed content related to suicidal thoughts in their conversation.",
                "action": "Please talk to your child immediately and consider contacting a mental health professional.",
                "resources": [
                    "National Suicide Prevention Lifeline: 988",
                    "Crisis Text Line: Text HOME to 741741"
                ]
            },
            "crisis_self_harm": {
                "title": "URGENT: Self-Harm Content Detected",
                "message": f"{user_name} expressed content related to self-harm in their conversation.",
                "action": "Please talk to your child immediately and consider contacting a mental health professional.",
                "resources": [
                    "Crisis Text Line: Text HOME to 741741"
                ]
            },
            "abuse_physical": {
                "title": "URGENT: Physical Abuse Reported",
                "message": f"{user_name} described what may be physical abuse in their conversation.",
                "action": "Please speak with your child immediately.",
                "resources": [
                    "Childhelp National Child Abuse Hotline: 1-800-422-4453",
                    "Call 911 if in immediate danger"
                ]
            },
        }

        template = category_messages.get(category, {
            "title": "Safety Alert",
            "message": f"Safety concern detected in {user_name}'s conversation.",
            "action": "Please review the conversation with your child.",
            "resources": []
        })

        resources_html = ""
        if template.get("resources"):
            resources_list = "".join([f"<li style='margin: 8px 0;'>{r}</li>" for r in template["resources"]])
            resources_html = f"""
            <div style='margin-top: 20px; padding: 15px; background-color: #f3f4f6; border-radius: 5px;'>
                <h3 style='margin-top: 0; color: #374151;'>Crisis Resources:</h3>
                <ul style='margin-bottom: 0; color: #4b5563;'>
                    {resources_list}
                </ul>
            </div>
            """

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style='font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.6; color: #1f2937; margin: 0; padding: 0;'>
    <div style='max-width: 600px; margin: 0 auto; padding: 20px;'>
        <div style='background-color: {color}; color: white; padding: 20px; border-radius: 8px 8px 0 0;'>
            <h1 style='margin: 0; font-size: 24px;'>{template['title']}</h1>
            <p style='margin: 10px 0 0 0; opacity: 0.9;'>
                {timestamp.strftime('%B %d, %Y at %I:%M %p')}
            </p>
        </div>

        <div style='background-color: #ffffff; padding: 30px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;'>
            <div style='background-color: #fef2f2; border-left: 4px solid {color}; padding: 15px; margin-bottom: 25px;'>
                <p style='margin: 0; color: #991b1b; font-weight: 600;'>
                    Severity: {severity.upper()}
                </p>
            </div>

            <h2 style='color: #111827; margin-top: 0;'>What Happened</h2>
            <p style='font-size: 16px; color: #374151;'>
                {template['message']}
            </p>

            <h2 style='color: #111827; margin-top: 30px;'>Recommended Action</h2>
            <p style='font-size: 16px; color: #374151;'>
                {template['action']}
            </p>

            {resources_html}

            <div style='margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;'>
                <p style='font-size: 14px; color: #6b7280; margin: 0;'>
                    This notification was generated automatically by the safety monitoring system.
                    You can review the full conversation details in the parent dashboard.
                </p>
            </div>
        </div>

        <div style='margin-top: 20px; text-align: center;'>
            <p style='font-size: 12px; color: #9ca3af;'>
                To disable these notifications, adjust your settings in the parent dashboard.
            </p>
        </div>
    </div>
</body>
</html>
"""
        return html

    def _generate_plain_text_summary(
        self,
        user_name: str,
        flags: List[Dict],
        summary_period: str
    ) -> str:
        """Generate plain text summary email"""
        total = len(flags)
        by_severity = {}
        by_type = {}

        for flag in flags:
            severity = flag.get("severity", "unknown")
            flag_type = flag.get("flag_type", "unknown")
            by_severity[severity] = by_severity.get(severity, 0) + 1
            by_type[flag_type] = by_type.get(flag_type, 0) + 1

        severity_summary = "\n".join([f"  - {s.title()}: {count}" for s, count in by_severity.items()])
        type_summary = "\n".join([f"  - {t.replace('_', ' ').title()}: {count}" for t, count in by_type.items()])

        body = f"""SAFETY SUMMARY - {summary_period.upper()}

Child: {user_name}
Period: {summary_period.title()}
Total Events: {total}

BY SEVERITY:
{severity_summary}

BY TYPE:
{type_summary}

Please review these events in the parent dashboard for more details.

---
This is an automated {summary_period} summary.
To adjust notification preferences, visit the parent dashboard.
"""
        return body

    def _generate_html_summary(
        self,
        user_name: str,
        flags: List[Dict],
        summary_period: str
    ) -> str:
        """Generate HTML summary email"""
        total = len(flags)
        by_severity = {}
        by_type = {}

        for flag in flags:
            severity = flag.get("severity", "unknown")
            flag_type = flag.get("flag_type", "unknown")
            by_severity[severity] = by_severity.get(severity, 0) + 1
            by_type[flag_type] = by_type.get(flag_type, 0) + 1

        severity_rows = "".join([
            f"<tr><td style='padding: 8px; border-bottom: 1px solid #e5e7eb;'>{s.title()}</td><td style='padding: 8px; border-bottom: 1px solid #e5e7eb; text-align: right;'>{count}</td></tr>"
            for s, count in by_severity.items()
        ])

        type_rows = "".join([
            f"<tr><td style='padding: 8px; border-bottom: 1px solid #e5e7eb;'>{t.replace('_', ' ').title()}</td><td style='padding: 8px; border-bottom: 1px solid #e5e7eb; text-align: right;'>{count}</td></tr>"
            for t, count in by_type.items()
        ])

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style='font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.6; color: #1f2937; margin: 0; padding: 0;'>
    <div style='max-width: 600px; margin: 0 auto; padding: 20px;'>
        <div style='background-color: #3b82f6; color: white; padding: 20px; border-radius: 8px 8px 0 0;'>
            <h1 style='margin: 0; font-size: 24px;'>Safety Summary - {summary_period.title()}</h1>
            <p style='margin: 10px 0 0 0; opacity: 0.9;'>{user_name}</p>
        </div>

        <div style='background-color: #ffffff; padding: 30px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;'>
            <div style='text-align: center; padding: 20px; background-color: #f3f4f6; border-radius: 8px; margin-bottom: 25px;'>
                <h2 style='margin: 0; font-size: 36px; color: #1f2937;'>{total}</h2>
                <p style='margin: 5px 0 0 0; color: #6b7280;'>Total Safety Events</p>
            </div>

            <h2 style='color: #111827; margin-top: 0;'>By Severity</h2>
            <table style='width: 100%; border-collapse: collapse;'>
                {severity_rows}
            </table>

            <h2 style='color: #111827; margin-top: 30px;'>By Type</h2>
            <table style='width: 100%; border-collapse: collapse;'>
                {type_rows}
            </table>

            <div style='margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;'>
                <p style='font-size: 14px; color: #6b7280; margin: 0;'>
                    Please review these events in the parent dashboard for more details.
                </p>
            </div>
        </div>

        <div style='margin-top: 20px; text-align: center;'>
            <p style='font-size: 12px; color: #9ca3af;'>
                This is an automated {summary_period} summary. To adjust notification preferences, visit the parent dashboard.
            </p>
        </div>
    </div>
</body>
</html>
"""
        return html


# Global instance
email_service = EmailService()


# Convenience functions
def send_email(
    to_email: str,
    subject: str,
    body: str,
    html_body: Optional[str] = None
) -> Dict:
    """Send an email notification"""
    return email_service.send_email(to_email, subject, body, html_body)


def send_critical_safety_alert(
    to_email: str,
    user_name: str,
    category: str,
    severity: str,
    details: Dict,
    timestamp: datetime,
    content_snippet: Optional[str] = None
) -> Dict:
    """Send a critical safety alert email"""
    return email_service.send_critical_safety_alert(
        to_email, user_name, category, severity, details, timestamp, content_snippet
    )


def send_bulk_safety_summary(
    to_email: str,
    user_name: str,
    flags: List[Dict],
    summary_period: str = "daily"
) -> Dict:
    """Send a bulk safety summary email"""
    return email_service.send_bulk_safety_summary(
        to_email, user_name, flags, summary_period
    )


def is_configured() -> bool:
    """Check if email service is configured"""
    return email_service.is_configured()
