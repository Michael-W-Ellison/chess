"""
Weekly Report Service
Generates periodic safety and activity reports for parents
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.safety import SafetyFlag
from models.conversation import Conversation, Message
from models.parent_preferences import ParentNotificationPreferences
from models.user import User
from services.email_service import email_service
from services.parent_preferences_service import parent_preferences_service

logger = logging.getLogger("chatbot.weekly_report")


class WeeklyReportService:
    """
    Service for generating periodic safety and activity reports

    Features:
    - Aggregate safety flags for a time period
    - Include conversation summaries
    - Calculate engagement statistics
    - Format and send comprehensive reports via email
    - Support both daily and weekly frequency

    Usage:
        report_service.generate_and_send_report(db, user_id=1, period="weekly")
    """

    def __init__(self):
        """Initialize WeeklyReportService"""
        logger.info("WeeklyReportService initialized")

    def generate_report_data(
        self,
        db: Session,
        user_id: int,
        period: str = "weekly"
    ) -> Dict:
        """
        Generate report data for a user

        Args:
            db: Database session
            user_id: User ID
            period: Report period ("daily" or "weekly")

        Returns:
            Dictionary containing all report data
        """
        # Calculate time range
        now = datetime.now()
        if period == "daily":
            start_date = now - timedelta(days=1)
            period_label = "Daily"
        elif period == "weekly":
            start_date = now - timedelta(days=7)
            period_label = "Weekly"
        else:
            raise ValueError(f"Invalid period: {period}. Must be 'daily' or 'weekly'")

        # Get user info
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        user_name = user.name or f"User {user_id}"

        # Aggregate safety flags
        safety_data = self._aggregate_safety_flags(db, user_id, start_date)

        # Aggregate conversation data
        conversation_data = self._aggregate_conversations(db, user_id, start_date)

        # Calculate engagement metrics
        engagement_data = self._calculate_engagement(db, user_id, start_date)

        logger.info(
            f"Generated {period} report for user {user_id}: "
            f"{safety_data['total_flags']} flags, {conversation_data['total_conversations']} conversations"
        )

        return {
            "user_id": user_id,
            "user_name": user_name,
            "period": period_label,
            "start_date": start_date.isoformat(),
            "end_date": now.isoformat(),
            "safety": safety_data,
            "conversations": conversation_data,
            "engagement": engagement_data,
        }

    def _aggregate_safety_flags(
        self,
        db: Session,
        user_id: int,
        start_date: datetime
    ) -> Dict:
        """
        Aggregate safety flag data for the period

        Args:
            db: Database session
            user_id: User ID
            start_date: Start of period

        Returns:
            Dictionary with safety flag statistics
        """
        # Get all flags in the period
        flags = (
            db.query(SafetyFlag)
            .filter(
                SafetyFlag.user_id == user_id,
                SafetyFlag.timestamp >= start_date
            )
            .order_by(SafetyFlag.timestamp.desc())
            .all()
        )

        # Aggregate by severity
        by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for flag in flags:
            severity = flag.severity.lower() if flag.severity else "low"
            if severity in by_severity:
                by_severity[severity] += 1

        # Aggregate by type
        by_type = {}
        for flag in flags:
            flag_type = flag.flag_type or "unknown"
            by_type[flag_type] = by_type.get(flag_type, 0) + 1

        # Get critical and high severity flags for detailed listing
        critical_flags = [
            {
                "id": f.id,
                "timestamp": f.timestamp.isoformat() if f.timestamp else None,
                "severity": f.severity,
                "flag_type": f.flag_type,
                "content_snippet": f.content_snippet[:100] if f.content_snippet else None,
            }
            for f in flags
            if f.severity and f.severity.lower() in ["critical", "high"]
        ]

        return {
            "total_flags": len(flags),
            "by_severity": by_severity,
            "by_type": by_type,
            "critical_and_high_flags": critical_flags[:10],  # Limit to 10 most recent
            "has_critical": by_severity["critical"] > 0,
            "has_high": by_severity["high"] > 0,
        }

    def _aggregate_conversations(
        self,
        db: Session,
        user_id: int,
        start_date: datetime
    ) -> Dict:
        """
        Aggregate conversation data for the period

        Args:
            db: Database session
            user_id: User ID
            start_date: Start of period

        Returns:
            Dictionary with conversation statistics and summaries
        """
        # Get conversations in the period
        conversations = (
            db.query(Conversation)
            .filter(
                Conversation.user_id == user_id,
                Conversation.start_time >= start_date
            )
            .order_by(Conversation.start_time.desc())
            .all()
        )

        # Count total messages
        total_messages = 0
        total_duration = 0
        moods = {}
        topics_set = set()

        # Collect summaries
        summaries = []

        for conv in conversations:
            # Count messages
            if conv.message_count:
                total_messages += conv.message_count

            # Add duration
            if conv.duration_seconds:
                total_duration += conv.duration_seconds

            # Track moods
            if conv.mood_detected:
                mood = conv.mood_detected.lower()
                moods[mood] = moods.get(mood, 0) + 1

            # Collect topics
            if conv.topics:
                topics_list = conv.get_topics()
                topics_set.update(topics_list)

            # Add summary if available
            if conv.conversation_summary:
                summaries.append({
                    "conversation_id": conv.id,
                    "start_time": conv.start_time.isoformat() if conv.start_time else None,
                    "summary": conv.conversation_summary,
                    "mood": conv.mood_detected,
                    "topics": conv.get_topics() if conv.topics else [],
                    "message_count": conv.message_count or 0,
                })

        # Determine primary mood
        primary_mood = "neutral"
        if moods:
            primary_mood = max(moods.items(), key=lambda x: x[1])[0]

        return {
            "total_conversations": len(conversations),
            "total_messages": total_messages,
            "total_duration_minutes": int(total_duration / 60) if total_duration else 0,
            "primary_mood": primary_mood,
            "mood_distribution": moods,
            "topics": list(topics_set)[:10],  # Top 10 topics
            "summaries": summaries[:5],  # Most recent 5 summaries
        }

    def _calculate_engagement(
        self,
        db: Session,
        user_id: int,
        start_date: datetime
    ) -> Dict:
        """
        Calculate engagement metrics

        Args:
            db: Database session
            user_id: User ID
            start_date: Start of period

        Returns:
            Dictionary with engagement metrics
        """
        # Count active days (days with at least one message)
        active_days_count = (
            db.query(func.date(Message.timestamp))
            .join(Conversation)
            .filter(
                Conversation.user_id == user_id,
                Message.timestamp >= start_date,
                Message.role == "user"
            )
            .distinct()
            .count()
        )

        # Count user messages
        user_message_count = (
            db.query(Message)
            .join(Conversation)
            .filter(
                Conversation.user_id == user_id,
                Message.timestamp >= start_date,
                Message.role == "user"
            )
            .count()
        )

        # Calculate average messages per session
        conversation_count = (
            db.query(Conversation)
            .filter(
                Conversation.user_id == user_id,
                Conversation.start_time >= start_date
            )
            .count()
        )

        avg_messages_per_session = 0
        if conversation_count > 0:
            avg_messages_per_session = round(user_message_count / conversation_count, 1)

        return {
            "active_days": active_days_count,
            "total_user_messages": user_message_count,
            "avg_messages_per_session": avg_messages_per_session,
        }

    def generate_and_send_report(
        self,
        db: Session,
        user_id: int,
        period: str = "weekly",
        force_send: bool = False
    ) -> Dict:
        """
        Generate report and send via email

        Args:
            db: Database session
            user_id: User ID
            period: Report period ("daily" or "weekly")
            force_send: If True, send regardless of preferences

        Returns:
            Dictionary with send result
        """
        # Get user and preferences
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        prefs = parent_preferences_service.get_preferences(db, user_id)

        # Check if reports are enabled (unless forced)
        if not force_send:
            if not prefs.email_notifications_enabled:
                logger.info(f"Email notifications disabled for user {user_id}")
                return {
                    "success": False,
                    "reason": "Email notifications disabled",
                    "sent": False
                }

            if prefs.summary_frequency == "none":
                logger.info(f"Summary reports disabled for user {user_id}")
                return {
                    "success": False,
                    "reason": "Summary reports disabled in preferences",
                    "sent": False
                }

            # Check if period matches preference
            if period == "daily" and prefs.summary_frequency != "daily":
                logger.info(f"Daily reports not enabled for user {user_id}")
                return {
                    "success": False,
                    "reason": "Daily reports not enabled",
                    "sent": False
                }

            if period == "weekly" and prefs.summary_frequency != "weekly":
                logger.info(f"Weekly reports not enabled for user {user_id}")
                return {
                    "success": False,
                    "reason": "Weekly reports not enabled",
                    "sent": False
                }

        # Get email address
        parent_email = prefs.email or user.parent_email
        if not parent_email:
            logger.warning(f"No parent email configured for user {user_id}")
            return {
                "success": False,
                "reason": "No parent email configured",
                "sent": False
            }

        # Generate report data
        report_data = self.generate_report_data(db, user_id, period)

        # Format report for email
        subject, plain_body, html_body = self._format_report_email(report_data, prefs)

        # Send email
        try:
            email_result = email_service.send_email(
                to_email=parent_email,
                subject=subject,
                body=plain_body,
                html_body=html_body
            )

            if email_result.get("sent"):
                logger.info(f"{period.title()} report sent to {parent_email} for user {user_id}")
                return {
                    "success": True,
                    "sent": True,
                    "to_email": parent_email,
                    "period": period,
                    "report_data": report_data
                }
            else:
                logger.error(f"Failed to send report: {email_result.get('error')}")
                return {
                    "success": False,
                    "sent": False,
                    "error": email_result.get("error", "Unknown error"),
                    "report_data": report_data
                }

        except Exception as e:
            logger.error(f"Exception sending report: {e}", exc_info=True)
            return {
                "success": False,
                "sent": False,
                "error": str(e),
                "report_data": report_data
            }

    def _format_report_email(
        self,
        report_data: Dict,
        prefs: ParentNotificationPreferences
    ) -> tuple:
        """
        Format report data as email

        Args:
            report_data: Report data dictionary
            prefs: Parent notification preferences

        Returns:
            Tuple of (subject, plain_body, html_body)
        """
        user_name = report_data["user_name"]
        period = report_data["period"]

        # Subject
        subject = f"Chess Tutor {period} Report - {user_name}"

        # Plain text body
        plain_body = self._generate_plain_text_report(report_data, prefs)

        # HTML body
        html_body = self._generate_html_report(report_data, prefs)

        return subject, plain_body, html_body

    def _generate_plain_text_report(
        self,
        report_data: Dict,
        prefs: ParentNotificationPreferences
    ) -> str:
        """
        Generate plain text email report

        Args:
            report_data: Report data
            prefs: Parent preferences

        Returns:
            Plain text report string
        """
        user_name = report_data["user_name"]
        period = report_data["period"]
        safety = report_data["safety"]
        conversations = report_data["conversations"]
        engagement = report_data["engagement"]

        # Build report sections
        sections = []

        # Header
        sections.append(f"CHESS TUTOR {period.upper()} REPORT")
        sections.append(f"Child: {user_name}")
        sections.append(f"Period: {period}")
        sections.append("")

        # Safety Summary
        sections.append("=" * 60)
        sections.append("SAFETY SUMMARY")
        sections.append("=" * 60)
        sections.append(f"Total Safety Flags: {safety['total_flags']}")

        if safety['total_flags'] > 0:
            sections.append("")
            sections.append("By Severity:")
            for severity, count in safety['by_severity'].items():
                if count > 0:
                    sections.append(f"  - {severity.title()}: {count}")

            sections.append("")
            sections.append("By Type:")
            for flag_type, count in safety['by_type'].items():
                sections.append(f"  - {flag_type.replace('_', ' ').title()}: {count}")

            # Critical/High flags details
            if safety['critical_and_high_flags']:
                sections.append("")
                sections.append("Critical & High Severity Flags:")
                for flag in safety['critical_and_high_flags'][:5]:
                    timestamp = flag['timestamp'][:10] if flag['timestamp'] else "Unknown"
                    sections.append(
                        f"  - [{timestamp}] {flag['severity'].upper()}: {flag['flag_type']}"
                    )
                    if prefs.include_content_snippets and flag['content_snippet']:
                        sections.append(f"    \"{flag['content_snippet']}\"")
        else:
            sections.append("✅ No safety flags during this period!")

        sections.append("")

        # Activity Summary
        sections.append("=" * 60)
        sections.append("ACTIVITY SUMMARY")
        sections.append("=" * 60)
        sections.append(f"Total Conversations: {conversations['total_conversations']}")
        sections.append(f"Total Messages: {conversations['total_messages']}")
        sections.append(f"Active Days: {engagement['active_days']}")
        sections.append(f"Avg Messages per Session: {engagement['avg_messages_per_session']}")

        if conversations['total_duration_minutes'] > 0:
            sections.append(f"Total Time: {conversations['total_duration_minutes']} minutes")

        if conversations['primary_mood']:
            sections.append(f"Primary Mood: {conversations['primary_mood'].title()}")

        if conversations['topics']:
            sections.append(f"Topics: {', '.join(conversations['topics'])}")

        sections.append("")

        # Conversation Summaries
        if conversations['summaries']:
            sections.append("=" * 60)
            sections.append("RECENT CONVERSATIONS")
            sections.append("=" * 60)

            for i, summary in enumerate(conversations['summaries'], 1):
                timestamp = summary['start_time'][:10] if summary['start_time'] else "Unknown"
                sections.append(f"{i}. [{timestamp}] {summary['message_count']} messages")
                sections.append(f"   {summary['summary']}")
                if summary['topics']:
                    sections.append(f"   Topics: {', '.join(summary['topics'])}")
                sections.append("")

        # Footer
        sections.append("=" * 60)
        sections.append("This is an automated report from the Chess Tutor Safety Monitoring System.")
        sections.append("To adjust report preferences, visit the parent dashboard.")

        return "\n".join(sections)

    def _generate_html_report(
        self,
        report_data: Dict,
        prefs: ParentNotificationPreferences
    ) -> str:
        """
        Generate HTML email report

        Args:
            report_data: Report data
            prefs: Parent preferences

        Returns:
            HTML report string
        """
        user_name = report_data["user_name"]
        period = report_data["period"]
        safety = report_data["safety"]
        conversations = report_data["conversations"]
        engagement = report_data["engagement"]

        # Determine overall status color
        if safety['has_critical']:
            status_color = "#dc2626"  # Red
            status_text = "Attention Required"
        elif safety['has_high']:
            status_color = "#ea580c"  # Orange
            status_text = "Review Recommended"
        elif safety['total_flags'] > 0:
            status_color = "#d97706"  # Yellow
            status_text = "Minor Concerns"
        else:
            status_color = "#16a34a"  # Green
            status_text = "All Clear"

        # Build safety flags HTML
        safety_flags_html = ""
        if safety['total_flags'] > 0:
            severity_rows = "".join([
                f"<tr><td style='padding: 8px; border-bottom: 1px solid #e5e7eb;'>{s.title()}</td>"
                f"<td style='padding: 8px; border-bottom: 1px solid #e5e7eb; text-align: right;'>{count}</td></tr>"
                for s, count in safety['by_severity'].items() if count > 0
            ])

            type_rows = "".join([
                f"<tr><td style='padding: 8px; border-bottom: 1px solid #e5e7eb;'>{t.replace('_', ' ').title()}</td>"
                f"<td style='padding: 8px; border-bottom: 1px solid #e5e7eb; text-align: right;'>{count}</td></tr>"
                for t, count in safety['by_type'].items()
            ])

            safety_flags_html = f"""
            <h2 style='color: #111827; margin-top: 30px;'>By Severity</h2>
            <table style='width: 100%; border-collapse: collapse;'>
                {severity_rows}
            </table>

            <h2 style='color: #111827; margin-top: 30px;'>By Type</h2>
            <table style='width: 100%; border-collapse: collapse;'>
                {type_rows}
            </table>
            """

            # Add critical/high flags details
            if safety['critical_and_high_flags']:
                flags_list = []
                for flag in safety['critical_and_high_flags'][:5]:
                    flag_type_formatted = flag['flag_type'].replace('_', ' ').title()
                    timestamp_formatted = flag['timestamp'][:16] if flag['timestamp'] else 'Unknown'
                    snippet_html = ''
                    if prefs.include_content_snippets and flag['content_snippet']:
                        snippet_html = f"<div style='margin-top: 8px; color: #374151; font-size: 14px;'>\"{flag['content_snippet']}\"</div>"

                    flags_list.append(f"""<div style='background-color: #fef2f2; border-left: 4px solid #dc2626; padding: 12px; margin-bottom: 10px;'>
                        <div style='font-weight: 600; color: #991b1b;'>{flag['severity'].upper()}: {flag_type_formatted}</div>
                        <div style='font-size: 12px; color: #6b7280; margin-top: 4px;'>{timestamp_formatted}</div>
                        {snippet_html}
                    </div>""")

                flags_list = "".join(flags_list)

                safety_flags_html += f"""
                <h2 style='color: #111827; margin-top: 30px;'>Critical & High Severity Flags</h2>
                {flags_list}
                """
        else:
            safety_flags_html = """
            <div style='background-color: #f0fdf4; border: 2px solid #16a34a; border-radius: 8px; padding: 20px; text-align: center;'>
                <div style='font-size: 48px; margin-bottom: 10px;'>✅</div>
                <div style='font-size: 18px; font-weight: 600; color: #16a34a;'>No Safety Flags</div>
                <div style='color: #15803d; margin-top: 5px;'>Everything looks great!</div>
            </div>
            """

        # Build conversation summaries HTML
        summaries_html = ""
        if conversations['summaries']:
            summaries_list = "".join([
                f"""<div style='background-color: #f9fafb; border-radius: 6px; padding: 15px; margin-bottom: 15px;'>
                    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;'>
                        <div style='font-weight: 600; color: #111827;'>Session {i}</div>
                        <div style='font-size: 12px; color: #6b7280;'>{summary['start_time'][:10] if summary['start_time'] else 'Unknown'} • {summary['message_count']} messages</div>
                    </div>
                    <div style='color: #374151; margin-bottom: 8px;'>{summary['summary']}</div>
                    {f"<div style='font-size: 12px; color: #6b7280;'>Topics: {', '.join(summary['topics'])}</div>" if summary['topics'] else ''}
                    {f"<div style='font-size: 12px; color: #6b7280; margin-top: 4px;'>Mood: {summary['mood'].title()}</div>" if summary.get('mood') else ''}
                </div>"""
                for i, summary in enumerate(conversations['summaries'], 1)
            ])

            summaries_html = f"""
            <h2 style='color: #111827; margin-top: 30px;'>Recent Conversations</h2>
            {summaries_list}
            """

        # Build complete HTML
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style='font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.6; color: #1f2937; margin: 0; padding: 0;'>
    <div style='max-width: 700px; margin: 0 auto; padding: 20px;'>
        <!-- Header -->
        <div style='background-color: #3b82f6; color: white; padding: 30px; border-radius: 8px 8px 0 0;'>
            <h1 style='margin: 0; font-size: 28px;'>Chess Tutor {period} Report</h1>
            <p style='margin: 10px 0 0 0; font-size: 18px; opacity: 0.9;'>{user_name}</p>
        </div>

        <!-- Status Badge -->
        <div style='background-color: {status_color}; color: white; padding: 15px; text-align: center;'>
            <div style='font-size: 16px; font-weight: 600;'>Status: {status_text}</div>
        </div>

        <!-- Main Content -->
        <div style='background-color: #ffffff; padding: 30px; border: 1px solid #e5e7eb; border-top: none;'>
            <!-- Activity Summary -->
            <h2 style='color: #111827; margin-top: 0;'>Activity Summary</h2>
            <div style='display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-bottom: 30px;'>
                <div style='background-color: #f3f4f6; padding: 15px; border-radius: 6px; text-align: center;'>
                    <div style='font-size: 32px; font-weight: 700; color: #3b82f6;'>{conversations['total_conversations']}</div>
                    <div style='font-size: 14px; color: #6b7280;'>Conversations</div>
                </div>
                <div style='background-color: #f3f4f6; padding: 15px; border-radius: 6px; text-align: center;'>
                    <div style='font-size: 32px; font-weight: 700; color: #3b82f6;'>{conversations['total_messages']}</div>
                    <div style='font-size: 14px; color: #6b7280;'>Messages</div>
                </div>
                <div style='background-color: #f3f4f6; padding: 15px; border-radius: 6px; text-align: center;'>
                    <div style='font-size: 32px; font-weight: 700; color: #3b82f6;'>{engagement['active_days']}</div>
                    <div style='font-size: 14px; color: #6b7280;'>Active Days</div>
                </div>
                <div style='background-color: #f3f4f6; padding: 15px; border-radius: 6px; text-align: center;'>
                    <div style='font-size: 32px; font-weight: 700; color: #3b82f6;'>{safety['total_flags']}</div>
                    <div style='font-size: 14px; color: #6b7280;'>Safety Flags</div>
                </div>
            </div>

            <!-- Mood & Topics -->
            {f"<div style='margin-bottom: 20px;'><strong>Primary Mood:</strong> {conversations['primary_mood'].title()}</div>" if conversations['primary_mood'] else ''}
            {f"<div style='margin-bottom: 30px;'><strong>Topics Discussed:</strong> {', '.join(conversations['topics'])}</div>" if conversations['topics'] else ''}

            <!-- Safety Flags -->
            <h2 style='color: #111827; margin-top: 30px;'>Safety Summary</h2>
            {safety_flags_html}

            <!-- Conversation Summaries -->
            {summaries_html}
        </div>

        <!-- Footer -->
        <div style='background-color: #f9fafb; padding: 20px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px; text-align: center;'>
            <p style='font-size: 14px; color: #6b7280; margin: 0;'>
                This is an automated report from the Chess Tutor Safety Monitoring System.
            </p>
            <p style='font-size: 12px; color: #9ca3af; margin: 10px 0 0 0;'>
                To adjust report preferences, visit the parent dashboard.
            </p>
        </div>
    </div>
</body>
</html>
"""
        return html


# Global service instance
weekly_report_service = WeeklyReportService()


# Convenience functions
def generate_report_data(
    db: Session, user_id: int, period: str = "weekly"
) -> Dict:
    """Generate report data for a user"""
    return weekly_report_service.generate_report_data(db, user_id, period)


def generate_and_send_report(
    db: Session, user_id: int, period: str = "weekly", force_send: bool = False
) -> Dict:
    """Generate and send report via email"""
    return weekly_report_service.generate_and_send_report(
        db, user_id, period, force_send
    )
