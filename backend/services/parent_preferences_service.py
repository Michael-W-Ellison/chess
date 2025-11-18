"""
Parent Notification Preferences Service
Manages parent notification preferences and settings
"""

import logging
from typing import Dict, Optional
from sqlalchemy.orm import Session

from models.parent_preferences import ParentNotificationPreferences
from models.user import User

logger = logging.getLogger("chatbot.parent_preferences")


class ParentPreferencesService:
    """
    Parent Preferences Service - manages parent notification preferences

    Features:
    - Get or create default preferences for a user
    - Update individual preference settings
    - Bulk update preferences
    - Check if notification should be sent based on preferences
    - Validate preference values

    Usage:
        prefs = parent_preferences_service.get_preferences(db, user_id=1)
        should_notify = parent_preferences_service.should_notify(
            db, user_id=1, severity="critical", flag_type="crisis"
        )
    """

    def __init__(self):
        """Initialize ParentPreferencesService"""
        logger.info("ParentPreferencesService initialized")

    def get_preferences(
        self, db: Session, user_id: int
    ) -> ParentNotificationPreferences:
        """
        Get parent notification preferences for a user
        Creates default preferences if none exist

        Args:
            db: Database session
            user_id: User ID

        Returns:
            ParentNotificationPreferences instance
        """
        return ParentNotificationPreferences.get_or_create_defaults(db, user_id)

    def update_preferences(
        self, db: Session, user_id: int, updates: Dict
    ) -> ParentNotificationPreferences:
        """
        Update parent notification preferences

        Args:
            db: Database session
            user_id: User ID
            updates: Dictionary of field updates

        Returns:
            Updated ParentNotificationPreferences instance
        """
        prefs = self.get_preferences(db, user_id)

        # Validate and update fields
        valid_fields = {
            # Email settings
            "email_notifications_enabled",
            # Severity filters
            "instant_notification_min_severity",
            "notify_on_critical",
            "notify_on_high",
            "notify_on_medium",
            "notify_on_low",
            # Type filters
            "notify_on_crisis",
            "notify_on_abuse",
            "notify_on_bullying",
            "notify_on_profanity",
            "notify_on_inappropriate",
            # Summary settings
            "summary_frequency",
            "summary_day_of_week",
            "summary_hour",
            # Content settings
            "include_content_snippets",
            "max_snippet_length",
            # Quiet hours
            "quiet_hours_enabled",
            "quiet_hours_start",
            "quiet_hours_end",
        }

        for field, value in updates.items():
            if field in valid_fields:
                # Validate specific fields
                if field == "instant_notification_min_severity":
                    if value not in ["low", "medium", "high", "critical"]:
                        raise ValueError(
                            f"Invalid severity: {value}. Must be low, medium, high, or critical"
                        )
                elif field == "summary_frequency":
                    if value not in ["daily", "weekly", "none"]:
                        raise ValueError(
                            f"Invalid summary frequency: {value}. Must be daily, weekly, or none"
                        )
                elif field == "summary_hour":
                    if not isinstance(value, int) or value < 0 or value > 23:
                        raise ValueError(
                            f"Invalid summary hour: {value}. Must be 0-23"
                        )
                elif field == "summary_day_of_week":
                    if value is not None and (
                        not isinstance(value, int) or value < 0 or value > 6
                    ):
                        raise ValueError(
                            f"Invalid day of week: {value}. Must be 0-6"
                        )
                elif field in ["quiet_hours_start", "quiet_hours_end"]:
                    if value is not None and (
                        not isinstance(value, int) or value < 0 or value > 23
                    ):
                        raise ValueError(
                            f"Invalid quiet hour: {value}. Must be 0-23 or None"
                        )

                setattr(prefs, field, value)
            else:
                logger.warning(f"Attempted to update invalid field: {field}")

        db.commit()
        db.refresh(prefs)

        logger.info(f"Updated preferences for user {user_id}")
        return prefs

    def update_severity_filters(
        self,
        db: Session,
        user_id: int,
        critical: Optional[bool] = None,
        high: Optional[bool] = None,
        medium: Optional[bool] = None,
        low: Optional[bool] = None,
    ) -> ParentNotificationPreferences:
        """
        Update severity notification filters

        Args:
            db: Database session
            user_id: User ID
            critical: Enable critical notifications
            high: Enable high severity notifications
            medium: Enable medium severity notifications
            low: Enable low severity notifications

        Returns:
            Updated ParentNotificationPreferences instance
        """
        updates = {}
        if critical is not None:
            updates["notify_on_critical"] = critical
        if high is not None:
            updates["notify_on_high"] = high
        if medium is not None:
            updates["notify_on_medium"] = medium
        if low is not None:
            updates["notify_on_low"] = low

        return self.update_preferences(db, user_id, updates)

    def update_type_filters(
        self,
        db: Session,
        user_id: int,
        crisis: Optional[bool] = None,
        abuse: Optional[bool] = None,
        bullying: Optional[bool] = None,
        profanity: Optional[bool] = None,
        inappropriate: Optional[bool] = None,
    ) -> ParentNotificationPreferences:
        """
        Update flag type notification filters

        Args:
            db: Database session
            user_id: User ID
            crisis: Enable crisis notifications
            abuse: Enable abuse notifications
            bullying: Enable bullying notifications
            profanity: Enable profanity notifications
            inappropriate: Enable inappropriate content notifications

        Returns:
            Updated ParentNotificationPreferences instance
        """
        updates = {}
        if crisis is not None:
            updates["notify_on_crisis"] = crisis
        if abuse is not None:
            updates["notify_on_abuse"] = abuse
        if bullying is not None:
            updates["notify_on_bullying"] = bullying
        if profanity is not None:
            updates["notify_on_profanity"] = profanity
        if inappropriate is not None:
            updates["notify_on_inappropriate"] = inappropriate

        return self.update_preferences(db, user_id, updates)

    def update_summary_settings(
        self,
        db: Session,
        user_id: int,
        frequency: Optional[str] = None,
        day_of_week: Optional[int] = None,
        hour: Optional[int] = None,
    ) -> ParentNotificationPreferences:
        """
        Update summary email settings

        Args:
            db: Database session
            user_id: User ID
            frequency: Summary frequency (daily, weekly, none)
            day_of_week: Day of week for weekly summaries (0=Monday, 6=Sunday)
            hour: Hour to send summary (0-23)

        Returns:
            Updated ParentNotificationPreferences instance
        """
        updates = {}
        if frequency is not None:
            updates["summary_frequency"] = frequency
        if day_of_week is not None:
            updates["summary_day_of_week"] = day_of_week
        if hour is not None:
            updates["summary_hour"] = hour

        return self.update_preferences(db, user_id, updates)

    def update_quiet_hours(
        self,
        db: Session,
        user_id: int,
        enabled: Optional[bool] = None,
        start: Optional[int] = None,
        end: Optional[int] = None,
    ) -> ParentNotificationPreferences:
        """
        Update quiet hours settings

        Args:
            db: Database session
            user_id: User ID
            enabled: Enable quiet hours
            start: Quiet hours start time (0-23)
            end: Quiet hours end time (0-23)

        Returns:
            Updated ParentNotificationPreferences instance
        """
        updates = {}
        if enabled is not None:
            updates["quiet_hours_enabled"] = enabled
        if start is not None:
            updates["quiet_hours_start"] = start
        if end is not None:
            updates["quiet_hours_end"] = end

        return self.update_preferences(db, user_id, updates)

    def should_notify(
        self, db: Session, user_id: int, severity: str, flag_type: str
    ) -> bool:
        """
        Check if parent should be notified for a given safety flag

        Args:
            db: Database session
            user_id: User ID
            severity: Flag severity (low, medium, high, critical)
            flag_type: Flag type (crisis, abuse, bullying, profanity, inappropriate_request)

        Returns:
            True if parent should be notified based on preferences
        """
        prefs = self.get_preferences(db, user_id)

        # Check if notification should be sent based on preferences
        if not prefs.should_notify_for_flag(severity, flag_type):
            logger.debug(
                f"Notification suppressed by preferences: user={user_id}, "
                f"severity={severity}, type={flag_type}"
            )
            return False

        # Check quiet hours
        if prefs.is_quiet_hours():
            logger.info(
                f"Notification suppressed due to quiet hours: user={user_id}"
            )
            return False

        return True

    def enable_all_notifications(
        self, db: Session, user_id: int
    ) -> ParentNotificationPreferences:
        """
        Enable all notification types and severities

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Updated ParentNotificationPreferences instance
        """
        updates = {
            "email_notifications_enabled": True,
            "notify_on_critical": True,
            "notify_on_high": True,
            "notify_on_medium": True,
            "notify_on_low": True,
            "notify_on_crisis": True,
            "notify_on_abuse": True,
            "notify_on_bullying": True,
            "notify_on_profanity": True,
            "notify_on_inappropriate": True,
        }

        return self.update_preferences(db, user_id, updates)

    def disable_all_notifications(
        self, db: Session, user_id: int
    ) -> ParentNotificationPreferences:
        """
        Disable all email notifications

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Updated ParentNotificationPreferences instance
        """
        updates = {"email_notifications_enabled": False}

        return self.update_preferences(db, user_id, updates)

    def reset_to_defaults(
        self, db: Session, user_id: int
    ) -> ParentNotificationPreferences:
        """
        Reset preferences to default values

        Args:
            db: Database session
            user_id: User ID

        Returns:
            ParentNotificationPreferences instance with default settings
        """
        # Delete existing preferences
        prefs = (
            db.query(ParentNotificationPreferences)
            .filter(ParentNotificationPreferences.user_id == user_id)
            .first()
        )

        if prefs:
            db.delete(prefs)
            db.commit()

        # Create new defaults
        return ParentNotificationPreferences.get_or_create_defaults(db, user_id)


# Global instance
parent_preferences_service = ParentPreferencesService()


# Convenience functions
def get_preferences(db: Session, user_id: int) -> ParentNotificationPreferences:
    """Get parent notification preferences"""
    return parent_preferences_service.get_preferences(db, user_id)


def update_preferences(
    db: Session, user_id: int, updates: Dict
) -> ParentNotificationPreferences:
    """Update parent notification preferences"""
    return parent_preferences_service.update_preferences(db, user_id, updates)


def should_notify(db: Session, user_id: int, severity: str, flag_type: str) -> bool:
    """Check if parent should be notified"""
    return parent_preferences_service.should_notify(db, user_id, severity, flag_type)


def enable_all_notifications(
    db: Session, user_id: int
) -> ParentNotificationPreferences:
    """Enable all notifications"""
    return parent_preferences_service.enable_all_notifications(db, user_id)


def disable_all_notifications(
    db: Session, user_id: int
) -> ParentNotificationPreferences:
    """Disable all notifications"""
    return parent_preferences_service.disable_all_notifications(db, user_id)


def reset_to_defaults(db: Session, user_id: int) -> ParentNotificationPreferences:
    """Reset preferences to defaults"""
    return parent_preferences_service.reset_to_defaults(db, user_id)
