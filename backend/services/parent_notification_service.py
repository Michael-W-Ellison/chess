"""
Parent Notification Service
Handles notifying parents about safety events and crisis situations

This service manages parent notifications for critical safety events,
including crisis detection (suicide, self-harm, abuse) and high-severity incidents.
"""

from typing import Dict, List, Optional
import logging
from datetime import datetime

from sqlalchemy.orm import Session
from models.safety import SafetyFlag
from models.conversation import Message
from models.user import User

logger = logging.getLogger("chatbot.parent_notification")


class ParentNotificationService:
    """
    Parent Notification Service - manages parent alerts for safety events

    Features:
    - Crisis event notifications (suicide, self-harm, abuse)
    - High-severity safety event notifications
    - Notification logging and tracking
    - Email/SMS integration points (to be implemented)
    - Notification preferences management

    Notification Triggers:
    - CRITICAL severity events (crisis, abuse)
    - HIGH severity events (severe profanity, high-severity inappropriate requests)
    - Parent requests for notification updates
    """

    def __init__(self):
        """Initialize ParentNotificationService"""
        self.notification_count = 0
        logger.info("ParentNotificationService initialized")

    def notify_crisis_event(
        self,
        user_id: int,
        conversation_id: int,
        safety_result: Dict,
        db: Session
    ) -> Dict:
        """
        Notify parent about a crisis event

        Args:
            user_id: User ID
            conversation_id: Conversation ID
            safety_result: Safety check result from SafetyFilter
            db: Database session

        Returns:
            Dictionary with notification result
        """
        # Get user info
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User {user_id} not found for crisis notification")
            return {"success": False, "error": "User not found"}

        # Extract crisis details
        flags = safety_result.get("flags", [])
        severity = safety_result.get("severity", "unknown")
        details = safety_result.get("details", {})
        original_message = safety_result.get("original_message", "")

        # Determine notification category
        notification_category = self._get_notification_category(flags, details)

        # Create notification record (in SafetyFlag table with parent_notified=True)
        self._log_parent_notification(
            user_id=user_id,
            conversation_id=conversation_id,
            category=notification_category,
            severity=severity,
            message_snippet=original_message[:100],
            db=db
        )

        # Format notification message for parent
        notification_message = self._format_crisis_notification(
            user_name=user.name or "Your child",
            category=notification_category,
            severity=severity,
            details=details,
            timestamp=datetime.now()
        )

        # Send notification (implementation depends on notification method)
        notification_result = self._send_notification(
            user_id=user_id,
            message=notification_message,
            category=notification_category,
            severity=severity,
            db=db
        )

        self.notification_count += 1

        logger.warning(
            f"PARENT NOTIFICATION: User {user_id}, Category: {notification_category}, "
            f"Severity: {severity}, Flags: {flags}"
        )

        return {
            "success": True,
            "notification_sent": notification_result["sent"],
            "category": notification_category,
            "severity": severity,
            "notification_id": notification_result.get("notification_id"),
        }

    def notify_high_severity_event(
        self,
        user_id: int,
        conversation_id: int,
        safety_result: Dict,
        db: Session
    ) -> Dict:
        """
        Notify parent about a high-severity (but not critical) event

        Args:
            user_id: User ID
            conversation_id: Conversation ID
            safety_result: Safety check result
            db: Database session

        Returns:
            Dictionary with notification result
        """
        # Similar to crisis notification but with different formatting
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"success": False, "error": "User not found"}

        flags = safety_result.get("flags", [])
        severity = safety_result.get("severity", "unknown")

        notification_category = "high_severity_content"

        # Log notification
        self._log_parent_notification(
            user_id=user_id,
            conversation_id=conversation_id,
            category=notification_category,
            severity=severity,
            message_snippet=safety_result.get("original_message", "")[:100],
            db=db
        )

        logger.info(
            f"Parent notification (high severity): User {user_id}, Flags: {flags}"
        )

        return {
            "success": True,
            "notification_sent": True,
            "category": notification_category,
            "severity": severity,
        }

    def _get_notification_category(self, flags: List[str], details: Dict) -> str:
        """
        Determine notification category from flags and details

        Args:
            flags: Safety flags (crisis, abuse, bullying, etc.)
            details: Detailed safety check results

        Returns:
            Notification category string
        """
        if "crisis" in flags:
            # Determine specific crisis category
            crisis_details = details.get("crisis", {})
            primary_category = crisis_details.get("primary_category", "")

            if primary_category == "suicide":
                return "crisis_suicide"
            elif primary_category == "self_harm":
                return "crisis_self_harm"
            else:
                return "crisis_general"

        elif "abuse" in flags:
            # Determine specific abuse category
            crisis_details = details.get("crisis", {})
            primary_category = crisis_details.get("primary_category", "")

            if primary_category == "abuse_physical":
                return "abuse_physical"
            elif primary_category == "abuse_emotional":
                return "abuse_emotional"
            elif primary_category == "abuse_sexual":
                return "abuse_sexual"
            else:
                return "abuse_general"

        elif "inappropriate_request" in flags:
            return "inappropriate_content"

        elif "profanity" in flags:
            return "severe_language"

        else:
            return "safety_concern"

    def _format_crisis_notification(
        self,
        user_name: str,
        category: str,
        severity: str,
        details: Dict,
        timestamp: datetime
    ) -> str:
        """
        Format crisis notification message for parent

        Args:
            user_name: User's name
            category: Notification category
            severity: Severity level
            details: Crisis details
            timestamp: Event timestamp

        Returns:
            Formatted notification message
        """
        category_messages = {
            "crisis_suicide": {
                "title": "URGENT: Suicide-Related Content Detected",
                "message": f"{user_name} expressed content related to suicidal thoughts in their conversation. This requires immediate attention.",
                "action": "Please talk to your child immediately and consider contacting a mental health professional. Crisis resources: National Suicide Prevention Lifeline (988)."
            },
            "crisis_self_harm": {
                "title": "URGENT: Self-Harm Content Detected",
                "message": f"{user_name} expressed content related to self-harm in their conversation. This requires immediate attention.",
                "action": "Please talk to your child immediately and consider contacting a mental health professional. Crisis resources: Crisis Text Line (text HOME to 741741)."
            },
            "abuse_physical": {
                "title": "URGENT: Physical Abuse Reported",
                "message": f"{user_name} described what may be physical abuse in their conversation. This requires immediate attention.",
                "action": "Please speak with your child immediately. If you suspect abuse, contact Childhelp National Child Abuse Hotline (1-800-422-4453) or call 911 if in immediate danger."
            },
            "abuse_emotional": {
                "title": "URGENT: Emotional Abuse Reported",
                "message": f"{user_name} described what may be emotional abuse in their conversation. This requires immediate attention.",
                "action": "Please speak with your child immediately. If you suspect abuse, contact Childhelp National Child Abuse Hotline (1-800-422-4453)."
            },
            "abuse_sexual": {
                "title": "URGENT: Sexual Abuse Reported",
                "message": f"{user_name} described what may be sexual abuse in their conversation. This requires immediate attention.",
                "action": "Please speak with your child immediately. If you suspect abuse, contact Childhelp (1-800-422-4453) or RAINN (1-800-656-4673), or call 911 if in immediate danger."
            },
            "crisis_general": {
                "title": "URGENT: Crisis Content Detected",
                "message": f"{user_name} expressed concerning content in their conversation that requires immediate attention.",
                "action": "Please talk to your child immediately and assess their well-being. Consider contacting a mental health professional."
            },
        }

        # Get category-specific message or use default
        notification_template = category_messages.get(category, {
            "title": "Safety Alert",
            "message": f"Safety concern detected in {user_name}'s conversation.",
            "action": "Please review the conversation with your child."
        })

        # Format full notification
        formatted_message = f"""
{notification_template['title']}

Time: {timestamp.strftime('%Y-%m-%d %I:%M %p')}
Severity: {severity.upper()}

{notification_template['message']}

RECOMMENDED ACTION:
{notification_template['action']}

This notification was generated automatically by the safety monitoring system. You can review the full conversation details in the parent dashboard.
"""

        return formatted_message.strip()

    def _send_notification(
        self,
        user_id: int,
        message: str,
        category: str,
        severity: str,
        db: Session
    ) -> Dict:
        """
        Send notification to parent (implementation stub)

        This is a placeholder for actual notification delivery.
        In production, this would send email, SMS, push notification, etc.

        Args:
            user_id: User ID
            message: Notification message
            category: Notification category
            severity: Severity level
            db: Database session

        Returns:
            Dictionary with send result
        """
        # TODO: Implement actual notification delivery
        # Options:
        # - Email via SMTP/SendGrid/AWS SES
        # - SMS via Twilio/AWS SNS
        # - Push notification via Firebase/OneSignal
        # - In-app notification flag

        # For now, just log it
        logger.critical(
            f"PARENT NOTIFICATION READY TO SEND:\n"
            f"User ID: {user_id}\n"
            f"Category: {category}\n"
            f"Severity: {severity}\n"
            f"Message:\n{message}"
        )

        return {
            "sent": True,  # Would be False if delivery failed
            "notification_id": f"notif_{user_id}_{datetime.now().timestamp()}",
            "delivery_method": "logged",  # Would be "email", "sms", etc.
        }

    def _log_parent_notification(
        self,
        user_id: int,
        conversation_id: int,
        category: str,
        severity: str,
        message_snippet: str,
        db: Session
    ) -> None:
        """
        Log parent notification in database

        Args:
            user_id: User ID
            conversation_id: Conversation ID
            category: Notification category
            severity: Severity level
            message_snippet: Snippet of the flagged message
            db: Database session
        """
        # Update the most recent SafetyFlag for this user to mark parent as notified
        recent_flag = (
            db.query(SafetyFlag)
            .filter(SafetyFlag.user_id == user_id)
            .order_by(SafetyFlag.timestamp.desc())
            .first()
        )

        if recent_flag:
            recent_flag.parent_notified = True
            db.commit()

        logger.info(
            f"Logged parent notification: user={user_id}, category={category}, "
            f"severity={severity}"
        )

    def get_notification_history(
        self, user_id: int, db: Session, limit: int = 10
    ) -> List[Dict]:
        """
        Get parent notification history for a user

        Args:
            user_id: User ID
            db: Database session
            limit: Maximum number of notifications to return

        Returns:
            List of notification records
        """
        # Get safety flags where parent was notified
        notified_flags = (
            db.query(SafetyFlag)
            .filter(SafetyFlag.user_id == user_id, SafetyFlag.parent_notified == True)
            .order_by(SafetyFlag.timestamp.desc())
            .limit(limit)
            .all()
        )

        notifications = []
        for flag in notified_flags:
            notifications.append({
                "timestamp": flag.timestamp.isoformat() if flag.timestamp else None,
                "severity": flag.severity,
                "flag_type": flag.flag_type,
                "content_snippet": flag.content_snippet,
                "action_taken": flag.action_taken,
            })

        return notifications

    def get_stats(self) -> Dict:
        """
        Get parent notification service statistics

        Returns:
            Dictionary with service stats
        """
        return {
            "notifications_sent_session": self.notification_count,
            "service_status": "active",
        }


# Global instance
parent_notification_service = ParentNotificationService()


# Convenience functions
def notify_crisis_event(
    user_id: int, conversation_id: int, safety_result: Dict, db: Session
) -> Dict:
    """Notify parent about crisis event"""
    return parent_notification_service.notify_crisis_event(
        user_id, conversation_id, safety_result, db
    )


def notify_high_severity_event(
    user_id: int, conversation_id: int, safety_result: Dict, db: Session
) -> Dict:
    """Notify parent about high-severity event"""
    return parent_notification_service.notify_high_severity_event(
        user_id, conversation_id, safety_result, db
    )


def get_notification_history(user_id: int, db: Session, limit: int = 10) -> List[Dict]:
    """Get notification history for user"""
    return parent_notification_service.get_notification_history(user_id, db, limit)


def get_stats() -> Dict:
    """Get service statistics"""
    return parent_notification_service.get_stats()
