"""
Parent Notification Preferences Model
Stores parent preferences for safety notifications
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, Dict, List

from database.database import Base


class ParentNotificationPreferences(Base):
    """
    Parent Notification Preferences model

    Stores parent preferences for receiving safety notifications
    Each user has one set of preferences for their parent

    Notification Triggers:
    - instant_notification_min_severity: Minimum severity for instant email
    - notify_on_critical: Send instant notifications for critical flags
    - notify_on_high: Send instant notifications for high severity flags
    - notify_on_medium: Send instant notifications for medium severity flags
    - notify_on_low: Send instant notifications for low severity flags

    Flag Type Filters:
    - notify_on_crisis: Notify for crisis flags (suicide, self-harm)
    - notify_on_abuse: Notify for abuse flags
    - notify_on_bullying: Notify for bullying flags
    - notify_on_profanity: Notify for profanity flags
    - notify_on_inappropriate: Notify for inappropriate content flags

    Summary Settings:
    - summary_frequency: How often to send summary emails (daily, weekly, none)
    - include_content_snippets: Include message snippets in notifications

    General Settings:
    - email_notifications_enabled: Master switch for email notifications
    - quiet_hours_start: Hour to start quiet period (0-23, null = disabled)
    - quiet_hours_end: Hour to end quiet period (0-23, null = disabled)
    """

    __tablename__ = "parent_notification_preferences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    # Email notification settings
    email = Column(String, nullable=True)  # Parent's email address
    email_notifications_enabled = Column(Boolean, default=True, nullable=False)

    # Instant notification severity filters
    instant_notification_min_severity = Column(String, default="high", nullable=False)  # low, medium, high, critical
    notify_on_critical = Column(Boolean, default=True, nullable=False)
    notify_on_high = Column(Boolean, default=True, nullable=False)
    notify_on_medium = Column(Boolean, default=False, nullable=False)
    notify_on_low = Column(Boolean, default=False, nullable=False)

    # Flag type filters
    notify_on_crisis = Column(Boolean, default=True, nullable=False)
    notify_on_abuse = Column(Boolean, default=True, nullable=False)
    notify_on_bullying = Column(Boolean, default=True, nullable=False)
    notify_on_profanity = Column(Boolean, default=False, nullable=False)
    notify_on_inappropriate = Column(Boolean, default=True, nullable=False)

    # Summary email settings
    summary_frequency = Column(String, default="weekly", nullable=False)  # daily, weekly, none
    summary_day_of_week = Column(Integer, default=0, nullable=True)  # 0=Monday, 6=Sunday (for weekly)
    summary_hour = Column(Integer, default=9, nullable=False)  # Hour to send summary (0-23)

    # Content settings
    include_content_snippets = Column(Boolean, default=True, nullable=False)
    max_snippet_length = Column(Integer, default=100, nullable=False)

    # Quiet hours (optional)
    quiet_hours_enabled = Column(Boolean, default=False, nullable=False)
    quiet_hours_start = Column(Integer, nullable=True)  # Hour 0-23
    quiet_hours_end = Column(Integer, nullable=True)  # Hour 0-23

    # Metadata
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    # Relationships
    user = relationship("User", back_populates="parent_preferences")

    def __repr__(self):
        return f"<ParentNotificationPreferences(user_id={self.user_id}, email_enabled={self.email_notifications_enabled})>"

    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "email": self.email,
            "email_notifications_enabled": self.email_notifications_enabled,
            "instant_notification_min_severity": self.instant_notification_min_severity,
            "severity_filters": {
                "critical": self.notify_on_critical,
                "high": self.notify_on_high,
                "medium": self.notify_on_medium,
                "low": self.notify_on_low,
            },
            "flag_type_filters": {
                "crisis": self.notify_on_crisis,
                "abuse": self.notify_on_abuse,
                "bullying": self.notify_on_bullying,
                "profanity": self.notify_on_profanity,
                "inappropriate": self.notify_on_inappropriate,
            },
            "summary_settings": {
                "frequency": self.summary_frequency,
                "day_of_week": self.summary_day_of_week,
                "hour": self.summary_hour,
            },
            "content_settings": {
                "include_snippets": self.include_content_snippets,
                "max_snippet_length": self.max_snippet_length,
            },
            "quiet_hours": {
                "enabled": self.quiet_hours_enabled,
                "start": self.quiet_hours_start,
                "end": self.quiet_hours_end,
            },
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def should_notify_for_flag(self, severity: str, flag_type: str) -> bool:
        """
        Check if parent should be notified for a given flag

        Args:
            severity: Flag severity (low, medium, high, critical)
            flag_type: Flag type (crisis, abuse, bullying, profanity, inappropriate_request)

        Returns:
            True if parent should be notified
        """
        # Check if email notifications are enabled
        if not self.email_notifications_enabled:
            return False

        # Check severity filter
        severity_enabled = {
            "critical": self.notify_on_critical,
            "high": self.notify_on_high,
            "medium": self.notify_on_medium,
            "low": self.notify_on_low,
        }.get(severity.lower(), False)

        if not severity_enabled:
            return False

        # Check flag type filter
        # Handle comma-separated flag types
        flag_types = [t.strip() for t in flag_type.split(",")]

        type_filters = {
            "crisis": self.notify_on_crisis,
            "abuse": self.notify_on_abuse,
            "bullying": self.notify_on_bullying,
            "profanity": self.notify_on_profanity,
            "inappropriate_request": self.notify_on_inappropriate,
            "inappropriate": self.notify_on_inappropriate,
        }

        # If any flag type is enabled, notify
        for ft in flag_types:
            if type_filters.get(ft.lower(), False):
                return True

        return False

    def is_quiet_hours(self) -> bool:
        """
        Check if current time is during quiet hours

        Returns:
            True if in quiet hours period
        """
        if not self.quiet_hours_enabled:
            return False

        if self.quiet_hours_start is None or self.quiet_hours_end is None:
            return False

        current_hour = datetime.now().hour

        # Handle quiet hours that span midnight
        if self.quiet_hours_start < self.quiet_hours_end:
            # Normal case: e.g., 22:00 to 08:00
            return self.quiet_hours_start <= current_hour < self.quiet_hours_end
        else:
            # Spans midnight: e.g., 22:00 to 08:00
            return current_hour >= self.quiet_hours_start or current_hour < self.quiet_hours_end

    @classmethod
    def get_or_create_defaults(cls, db, user_id: int) -> "ParentNotificationPreferences":
        """
        Get existing preferences or create with defaults

        Args:
            db: Database session
            user_id: User ID

        Returns:
            ParentNotificationPreferences instance
        """
        prefs = db.query(cls).filter(cls.user_id == user_id).first()

        if not prefs:
            prefs = cls(
                user_id=user_id,
                email_notifications_enabled=True,
                instant_notification_min_severity="high",
                notify_on_critical=True,
                notify_on_high=True,
                notify_on_medium=False,
                notify_on_low=False,
                notify_on_crisis=True,
                notify_on_abuse=True,
                notify_on_bullying=True,
                notify_on_profanity=False,
                notify_on_inappropriate=True,
                summary_frequency="weekly",
                summary_day_of_week=0,  # Monday
                summary_hour=9,
                include_content_snippets=True,
                max_snippet_length=100,
                quiet_hours_enabled=False,
            )
            db.add(prefs)
            db.commit()
            db.refresh(prefs)

        return prefs
