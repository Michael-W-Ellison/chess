"""
Safety Flag Service
Comprehensive service for creating, retrieving, and managing safety flags

This service provides functionality for:
- Creating and storing safety flags
- Retrieving flags with various filters
- Marking parents as notified
- Getting safety statistics
- Managing flag lifecycle
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from models.safety import SafetyFlag
from models.user import User

logger = logging.getLogger("chatbot.safety_flag_service")


class SafetyFlagService:
    """
    SafetyFlagService - Comprehensive safety flag management

    Provides CRUD operations and analytics for safety flags.
    Works alongside SafetyFilter to provide complete safety monitoring.
    """

    def create_flag(
        self,
        db: Session,
        user_id: int,
        flag_type: str,
        severity: str,
        content_snippet: Optional[str] = None,
        action_taken: Optional[str] = None,
        message_id: Optional[int] = None,
        notify_parent: bool = False
    ) -> SafetyFlag:
        """
        Create and store a new safety flag

        Args:
            db: Database session
            user_id: ID of the user
            flag_type: Type of flag (crisis, profanity, bullying, inappropriate_request, abuse)
            severity: Severity level (low, medium, high, critical)
            content_snippet: First 100 chars of flagged content
            action_taken: Action taken by system (allow, warn, block, etc.)
            message_id: Optional message ID this flag is associated with
            notify_parent: Whether parent should be notified

        Returns:
            Created SafetyFlag object
        """
        flag = SafetyFlag(
            user_id=user_id,
            message_id=message_id,
            flag_type=flag_type,
            severity=severity,
            content_snippet=content_snippet[:100] if content_snippet else None,
            action_taken=action_taken,
            timestamp=datetime.now(),
            parent_notified=False
        )

        db.add(flag)
        db.commit()
        db.refresh(flag)

        logger.info(
            f"Safety flag created: id={flag.id}, user={user_id}, "
            f"type={flag_type}, severity={severity}"
        )

        return flag

    def get_by_id(self, db: Session, flag_id: int) -> Optional[SafetyFlag]:
        """
        Get a safety flag by ID

        Args:
            db: Database session
            flag_id: Flag ID

        Returns:
            SafetyFlag object or None
        """
        return db.query(SafetyFlag).filter(SafetyFlag.id == flag_id).first()

    def get_by_user(
        self,
        db: Session,
        user_id: int,
        limit: Optional[int] = None,
        offset: int = 0,
        since_date: Optional[datetime] = None
    ) -> List[SafetyFlag]:
        """
        Get all safety flags for a user

        Args:
            db: Database session
            user_id: User ID
            limit: Optional limit on number of results
            offset: Number of results to skip
            since_date: Optional date filter (flags after this date)

        Returns:
            List of SafetyFlag objects ordered by timestamp (newest first)
        """
        query = db.query(SafetyFlag).filter(
            SafetyFlag.user_id == user_id
        )

        if since_date:
            query = query.filter(SafetyFlag.timestamp >= since_date)

        query = query.order_by(SafetyFlag.timestamp.desc())

        if limit:
            query = query.limit(limit).offset(offset)

        return query.all()

    def get_by_severity(
        self,
        db: Session,
        severity: str,
        user_id: Optional[int] = None,
        since_date: Optional[datetime] = None
    ) -> List[SafetyFlag]:
        """
        Get flags by severity level

        Args:
            db: Database session
            severity: Severity level to filter by
            user_id: Optional user ID filter
            since_date: Optional date filter (flags after this date)

        Returns:
            List of SafetyFlag objects
        """
        query = db.query(SafetyFlag).filter(SafetyFlag.severity == severity)

        if user_id:
            query = query.filter(SafetyFlag.user_id == user_id)

        if since_date:
            query = query.filter(SafetyFlag.timestamp >= since_date)

        return query.order_by(SafetyFlag.timestamp.desc()).all()

    def get_critical_flags(
        self,
        db: Session,
        user_id: Optional[int] = None,
        since_date: Optional[datetime] = None,
        include_notified: bool = False
    ) -> List[SafetyFlag]:
        """
        Get all critical severity flags

        Args:
            db: Database session
            user_id: Optional user ID filter
            since_date: Optional date filter
            include_notified: Whether to include flags where parent was already notified

        Returns:
            List of critical SafetyFlag objects
        """
        query = db.query(SafetyFlag).filter(SafetyFlag.severity == "critical")

        if user_id:
            query = query.filter(SafetyFlag.user_id == user_id)

        if since_date:
            query = query.filter(SafetyFlag.timestamp >= since_date)

        if not include_notified:
            query = query.filter(SafetyFlag.parent_notified == False)

        return query.order_by(SafetyFlag.timestamp.desc()).all()

    def get_by_type(
        self,
        db: Session,
        flag_type: str,
        user_id: Optional[int] = None,
        since_date: Optional[datetime] = None
    ) -> List[SafetyFlag]:
        """
        Get flags by type

        Args:
            db: Database session
            flag_type: Flag type to filter by
            user_id: Optional user ID filter
            since_date: Optional date filter

        Returns:
            List of SafetyFlag objects
        """
        # Handle comma-separated flag types (e.g., "crisis,abuse")
        if "," in flag_type:
            query = db.query(SafetyFlag).filter(
                SafetyFlag.flag_type.contains(flag_type)
            )
        else:
            query = db.query(SafetyFlag).filter(
                SafetyFlag.flag_type.contains(flag_type)
            )

        if user_id:
            query = query.filter(SafetyFlag.user_id == user_id)

        if since_date:
            query = query.filter(SafetyFlag.timestamp >= since_date)

        return query.order_by(SafetyFlag.timestamp.desc()).all()

    def get_unnotified_flags(
        self,
        db: Session,
        user_id: Optional[int] = None,
        min_severity: Optional[str] = None
    ) -> List[SafetyFlag]:
        """
        Get flags where parent has not been notified

        Args:
            db: Database session
            user_id: Optional user ID filter
            min_severity: Optional minimum severity (e.g., "high" includes "high" and "critical")

        Returns:
            List of SafetyFlag objects where parent_notified is False
        """
        query = db.query(SafetyFlag).filter(SafetyFlag.parent_notified == False)

        if user_id:
            query = query.filter(SafetyFlag.user_id == user_id)

        if min_severity:
            severity_order = ["low", "medium", "high", "critical"]
            if min_severity in severity_order:
                min_index = severity_order.index(min_severity)
                allowed_severities = severity_order[min_index:]
                query = query.filter(SafetyFlag.severity.in_(allowed_severities))

        return query.order_by(SafetyFlag.timestamp.desc()).all()

    def mark_parent_notified(
        self,
        db: Session,
        flag_id: int
    ) -> Optional[SafetyFlag]:
        """
        Mark a flag as parent notified

        Args:
            db: Database session
            flag_id: Flag ID to update

        Returns:
            Updated SafetyFlag object or None if not found
        """
        flag = self.get_by_id(db, flag_id)
        if flag:
            flag.parent_notified = True
            db.commit()
            db.refresh(flag)
            logger.info(f"Flag {flag_id} marked as parent notified")
        return flag

    def mark_multiple_parent_notified(
        self,
        db: Session,
        flag_ids: List[int]
    ) -> int:
        """
        Mark multiple flags as parent notified

        Args:
            db: Database session
            flag_ids: List of flag IDs to update

        Returns:
            Number of flags updated
        """
        count = db.query(SafetyFlag).filter(
            SafetyFlag.id.in_(flag_ids)
        ).update(
            {"parent_notified": True},
            synchronize_session=False
        )
        db.commit()

        logger.info(f"Marked {count} flags as parent notified")
        return count

    def get_recent_flags(
        self,
        db: Session,
        hours: int = 24,
        user_id: Optional[int] = None
    ) -> List[SafetyFlag]:
        """
        Get flags from the last N hours

        Args:
            db: Database session
            hours: Number of hours to look back
            user_id: Optional user ID filter

        Returns:
            List of SafetyFlag objects from the last N hours
        """
        since_date = datetime.now() - timedelta(hours=hours)
        query = db.query(SafetyFlag).filter(SafetyFlag.timestamp >= since_date)

        if user_id:
            query = query.filter(SafetyFlag.user_id == user_id)

        return query.order_by(SafetyFlag.timestamp.desc()).all()

    def get_stats(
        self,
        db: Session,
        user_id: Optional[int] = None,
        since_date: Optional[datetime] = None
    ) -> Dict:
        """
        Get comprehensive safety flag statistics

        Args:
            db: Database session
            user_id: Optional user ID filter
            since_date: Optional date filter

        Returns:
            Dictionary with various statistics
        """
        query = db.query(SafetyFlag)

        if user_id:
            query = query.filter(SafetyFlag.user_id == user_id)

        if since_date:
            query = query.filter(SafetyFlag.timestamp >= since_date)

        # Total count
        total_count = query.count()

        # Count by severity
        severity_counts = {}
        for severity in ["low", "medium", "high", "critical"]:
            count = query.filter(SafetyFlag.severity == severity).count()
            severity_counts[severity] = count

        # Count by type
        type_counts = {}
        for flag_type in ["crisis", "profanity", "bullying", "inappropriate_request", "abuse"]:
            count = query.filter(SafetyFlag.flag_type.contains(flag_type)).count()
            if count > 0:
                type_counts[flag_type] = count

        # Parent notification stats
        notified_count = query.filter(SafetyFlag.parent_notified == True).count()
        unnotified_count = query.filter(SafetyFlag.parent_notified == False).count()

        # Recent activity (last 24 hours)
        recent_cutoff = datetime.now() - timedelta(hours=24)
        recent_count = query.filter(SafetyFlag.timestamp >= recent_cutoff).count()

        return {
            "total_flags": total_count,
            "by_severity": severity_counts,
            "by_type": type_counts,
            "parent_notified": notified_count,
            "parent_unnotified": unnotified_count,
            "last_24_hours": recent_count,
        }

    def get_user_safety_summary(
        self,
        db: Session,
        user_id: int
    ) -> Dict:
        """
        Get comprehensive safety summary for a user

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Dictionary with user's safety summary
        """
        # All-time stats
        all_time_stats = self.get_stats(db, user_id=user_id)

        # Recent stats (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        recent_stats = self.get_stats(db, user_id=user_id, since_date=week_ago)

        # Critical flags needing attention
        critical_unnotified = self.get_critical_flags(
            db, user_id=user_id, include_notified=False
        )

        # Most recent flag
        recent_flags = self.get_by_user(db, user_id=user_id, limit=1)
        most_recent = recent_flags[0] if recent_flags else None

        return {
            "user_id": user_id,
            "all_time": all_time_stats,
            "last_7_days": recent_stats,
            "critical_needing_attention": len(critical_unnotified),
            "most_recent_flag": most_recent.to_dict() if most_recent else None,
        }

    def delete_old_flags(
        self,
        db: Session,
        days_old: int = 365,
        exclude_critical: bool = True
    ) -> int:
        """
        Delete flags older than specified days (for database maintenance)

        Args:
            db: Database session
            days_old: Delete flags older than this many days
            exclude_critical: Whether to exclude critical flags from deletion

        Returns:
            Number of flags deleted
        """
        cutoff_date = datetime.now() - timedelta(days=days_old)
        query = db.query(SafetyFlag).filter(SafetyFlag.timestamp < cutoff_date)

        if exclude_critical:
            query = query.filter(SafetyFlag.severity != "critical")

        count = query.delete(synchronize_session=False)
        db.commit()

        logger.info(f"Deleted {count} safety flags older than {days_old} days")
        return count


# Global instance
safety_flag_service = SafetyFlagService()


# Convenience functions
def create_flag(
    db: Session,
    user_id: int,
    flag_type: str,
    severity: str,
    content_snippet: Optional[str] = None,
    action_taken: Optional[str] = None,
    message_id: Optional[int] = None,
    notify_parent: bool = False
) -> SafetyFlag:
    """Create a new safety flag"""
    return safety_flag_service.create_flag(
        db, user_id, flag_type, severity, content_snippet,
        action_taken, message_id, notify_parent
    )


def get_by_user(db: Session, user_id: int, limit: Optional[int] = None) -> List[SafetyFlag]:
    """Get all safety flags for a user"""
    return safety_flag_service.get_by_user(db, user_id, limit)


def get_critical_flags(
    db: Session,
    user_id: Optional[int] = None,
    since_date: Optional[datetime] = None
) -> List[SafetyFlag]:
    """Get critical severity flags"""
    return safety_flag_service.get_critical_flags(db, user_id, since_date)


def mark_parent_notified(db: Session, flag_id: int) -> Optional[SafetyFlag]:
    """Mark a flag as parent notified"""
    return safety_flag_service.mark_parent_notified(db, flag_id)


def get_stats(db: Session, user_id: Optional[int] = None) -> Dict:
    """Get safety flag statistics"""
    return safety_flag_service.get_stats(db, user_id)


def get_user_safety_summary(db: Session, user_id: int) -> Dict:
    """Get comprehensive safety summary for a user"""
    return safety_flag_service.get_user_safety_summary(db, user_id)
