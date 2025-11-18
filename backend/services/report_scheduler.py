"""
Report Scheduler Service
Automatically sends weekly/daily reports based on user preferences
"""

import logging
from datetime import datetime, time as dt_time
from typing import List
from sqlalchemy.orm import Session

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from database.database import SessionLocal
from models.user import User
from models.parent_preferences import ParentNotificationPreferences
from services.weekly_report_service import weekly_report_service
from utils.config import settings

logger = logging.getLogger("chatbot.report_scheduler")


class ReportScheduler:
    """
    Automated Report Scheduler

    Features:
    - Background scheduler that runs hourly
    - Checks all users for due weekly/daily reports
    - Sends reports based on user preferences
    - Respects configured day of week and hour
    - Handles timezone considerations

    Usage:
        scheduler = ReportScheduler()
        scheduler.start()
        # ... when shutting down
        scheduler.stop()
    """

    def __init__(self):
        """Initialize ReportScheduler"""
        self.scheduler = BackgroundScheduler()
        self.enabled = settings.ENABLE_WEEKLY_REPORTS and settings.ENABLE_PARENT_NOTIFICATIONS
        logger.info(
            f"ReportScheduler initialized - Enabled: {self.enabled}, "
            f"Weekly Reports: {settings.ENABLE_WEEKLY_REPORTS}, "
            f"Notifications: {settings.ENABLE_PARENT_NOTIFICATIONS}"
        )

    def start(self):
        """
        Start the scheduler

        Sets up a cron job to run every hour at minute 0
        """
        if not self.enabled:
            logger.info("Report scheduler disabled - skipping start")
            return

        # Run every hour at minute 0
        self.scheduler.add_job(
            self.check_and_send_reports,
            trigger=CronTrigger(minute=0),  # Every hour at :00
            id='report_checker',
            name='Check and send scheduled reports',
            replace_existing=True
        )

        self.scheduler.start()
        logger.info("Report scheduler started - checking for due reports every hour")

    def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Report scheduler stopped")

    def check_and_send_reports(self):
        """
        Check all users and send reports if due

        This method:
        1. Gets current day of week and hour
        2. Queries all users with active preferences
        3. Checks if each user is due for a report
        4. Sends reports for users who are due
        """
        logger.info("Starting scheduled report check")

        # Create database session
        db = SessionLocal()

        try:
            # Get current time
            now = datetime.now()
            current_day = now.weekday()  # 0=Monday, 6=Sunday
            current_hour = now.hour

            logger.debug(f"Current time: Day {current_day}, Hour {current_hour}")

            # Get all users with email notifications enabled
            users_to_check = self._get_users_with_reports_enabled(db)

            logger.info(f"Found {len(users_to_check)} users with reports enabled")

            # Check each user
            sent_count = 0
            skipped_count = 0
            error_count = 0

            for user_id, prefs in users_to_check:
                try:
                    # Check if report is due
                    if self._is_report_due(prefs, current_day, current_hour):
                        period = prefs.summary_frequency  # "daily" or "weekly"

                        logger.info(
                            f"Sending {period} report for user {user_id} "
                            f"(scheduled for day={prefs.summary_day_of_week}, hour={prefs.summary_hour})"
                        )

                        # Send the report
                        result = weekly_report_service.generate_and_send_report(
                            db, user_id, period, force_send=False
                        )

                        if result.get("sent"):
                            sent_count += 1
                            logger.info(f"Successfully sent {period} report to user {user_id}")
                        else:
                            skipped_count += 1
                            reason = result.get("reason") or result.get("error")
                            logger.warning(f"Report not sent for user {user_id}: {reason}")

                except Exception as e:
                    error_count += 1
                    logger.error(f"Error sending report for user {user_id}: {e}", exc_info=True)

            logger.info(
                f"Report check complete - Sent: {sent_count}, Skipped: {skipped_count}, Errors: {error_count}"
            )

        except Exception as e:
            logger.error(f"Error in scheduled report check: {e}", exc_info=True)

        finally:
            db.close()

    def _get_users_with_reports_enabled(self, db: Session) -> List[tuple]:
        """
        Get all users with email reports enabled

        Args:
            db: Database session

        Returns:
            List of (user_id, preferences) tuples
        """
        # Query users with email notifications and summaries enabled
        preferences = (
            db.query(ParentNotificationPreferences)
            .filter(
                ParentNotificationPreferences.email_notifications_enabled == True,
                ParentNotificationPreferences.summary_frequency.in_(["daily", "weekly"]),
                ParentNotificationPreferences.email.isnot(None)
            )
            .all()
        )

        return [(pref.user_id, pref) for pref in preferences]

    def _is_report_due(
        self,
        prefs: ParentNotificationPreferences,
        current_day: int,
        current_hour: int
    ) -> bool:
        """
        Check if a report is due for a user

        Args:
            prefs: User's notification preferences
            current_day: Current day of week (0=Monday, 6=Sunday)
            current_hour: Current hour (0-23)

        Returns:
            True if report should be sent now
        """
        # Check hour match
        if current_hour != prefs.summary_hour:
            return False

        # For daily reports, send every day at the configured hour
        if prefs.summary_frequency == "daily":
            logger.debug(f"User {prefs.user_id}: Daily report due (hour={current_hour})")
            return True

        # For weekly reports, check day of week
        if prefs.summary_frequency == "weekly":
            if current_day == prefs.summary_day_of_week:
                logger.debug(
                    f"User {prefs.user_id}: Weekly report due "
                    f"(day={current_day}, hour={current_hour})"
                )
                return True
            else:
                logger.debug(
                    f"User {prefs.user_id}: Not due yet "
                    f"(current_day={current_day}, scheduled_day={prefs.summary_day_of_week})"
                )
                return False

        return False

    def force_check_now(self):
        """
        Force an immediate check for due reports (for testing)

        This can be called manually for testing purposes
        """
        logger.info("Forcing immediate report check")
        self.check_and_send_reports()


# Global scheduler instance
report_scheduler = ReportScheduler()


# Convenience functions
def start_scheduler():
    """Start the report scheduler"""
    report_scheduler.start()


def stop_scheduler():
    """Stop the report scheduler"""
    report_scheduler.stop()


def force_check():
    """Force immediate check for due reports"""
    report_scheduler.force_check_now()
