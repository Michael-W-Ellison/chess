"""
Conversation Tracker Service
Tracks conversation metrics, streaks, and awards friendship points
"""

from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import func
from models.personality import BotPersonality
from models.conversation import Conversation, Message
from services.friendship_progression import add_friendship_points

logger = logging.getLogger("chatbot.conversation_tracker")


class ConversationTracker:
    """
    Conversation Tracker - tracks conversations and awards friendship points

    Responsibilities:
    - Track daily check-ins and streaks
    - Award friendship points for conversation activities
    - Calculate conversation quality metrics
    - Provide conversation analytics
    """

    def on_conversation_start(
        self,
        user_id: int,
        personality: BotPersonality,
        db: Session
    ) -> Dict:
        """
        Handle conversation start event
        Awards points for daily check-in and streaks

        Args:
            user_id: User ID
            personality: BotPersonality object
            db: Database session

        Returns:
            Dictionary with check-in info and points awarded
        """
        result = {
            "is_first_today": False,
            "streak_days": 0,
            "points_awarded": [],
            "streak_bonus": False,
        }

        # Check if this is first conversation today
        is_first_today = self.is_first_conversation_today(user_id, db)

        if is_first_today:
            result["is_first_today"] = True

            # Award daily check-in points
            _, _, event = add_friendship_points(
                personality, "daily_checkin", db
            )
            result["points_awarded"].append({
                "activity": "daily_checkin",
                "points": event["points_earned"]
            })

            # Calculate streak
            streak_days = self.calculate_streak(user_id, db)
            result["streak_days"] = streak_days

            # Award streak bonuses
            if streak_days >= 30:
                _, _, event = add_friendship_points(
                    personality, "streak_30_days", db
                )
                result["points_awarded"].append({
                    "activity": "streak_30_days",
                    "points": event["points_earned"]
                })
                result["streak_bonus"] = True
            elif streak_days >= 7:
                _, _, event = add_friendship_points(
                    personality, "streak_7_days", db
                )
                result["points_awarded"].append({
                    "activity": "streak_7_days",
                    "points": event["points_earned"]
                })
                result["streak_bonus"] = True
            elif streak_days >= 3:
                _, _, event = add_friendship_points(
                    personality, "streak_3_days", db
                )
                result["points_awarded"].append({
                    "activity": "streak_3_days",
                    "points": event["points_earned"]
                })
                result["streak_bonus"] = True

            logger.info(
                f"Daily check-in for user {user_id}, streak: {streak_days} days"
            )

        return result

    def on_message_sent(
        self,
        user_id: int,
        personality: BotPersonality,
        message: str,
        db: Session
    ) -> Dict:
        """
        Handle message sent event
        Awards points for message and detects special activities

        Args:
            user_id: User ID
            personality: BotPersonality object
            message: User's message content
            db: Database session

        Returns:
            Dictionary with points awarded and activities detected
        """
        result = {
            "points_awarded": [],
            "activities_detected": [],
        }

        # Award points for message
        _, _, event = add_friendship_points(
            personality, "message_sent", db
        )
        result["points_awarded"].append({
            "activity": "message_sent",
            "points": event["points_earned"]
        })

        message_lower = message.lower()

        # Check for thanks/gratitude
        if any(word in message_lower for word in ["thank", "thanks", "thx", "ty"]):
            _, _, event = add_friendship_points(
                personality, "thanks_bot", db
            )
            result["points_awarded"].append({
                "activity": "thanks_bot",
                "points": event["points_earned"]
            })
            result["activities_detected"].append("thanked_bot")

        # Check for laughter
        if any(word in message_lower for word in ["lol", "haha", "hehe", "funny", "😂"]):
            _, _, event = add_friendship_points(
                personality, "laughs_at_joke", db
            )
            result["points_awarded"].append({
                "activity": "laughs_at_joke",
                "points": event["points_earned"]
            })
            result["activities_detected"].append("laughed")

        # Check for sharing feelings
        feeling_words = [
            "feel", "feeling", "sad", "happy", "excited", "worried",
            "anxious", "scared", "nervous", "proud", "angry", "upset"
        ]
        if any(word in message_lower for word in feeling_words):
            _, _, event = add_friendship_points(
                personality, "shares_feelings", db
            )
            result["points_awarded"].append({
                "activity": "shares_feelings",
                "points": event["points_earned"]
            })
            result["activities_detected"].append("shared_feelings")

        # Check for asking advice
        advice_phrases = [
            "what should i", "should i", "advice", "what do you think",
            "help me", "can you help"
        ]
        if any(phrase in message_lower for phrase in advice_phrases):
            _, _, event = add_friendship_points(
                personality, "asks_for_advice", db
            )
            result["points_awarded"].append({
                "activity": "asks_for_advice",
                "points": event["points_earned"]
            })
            result["activities_detected"].append("asked_advice")

        # Check for positive feedback
        positive_phrases = [
            "you're great", "you're awesome", "you're the best",
            "love talking to you", "you're cool", "you're nice",
            "you're helpful"
        ]
        if any(phrase in message_lower for phrase in positive_phrases):
            _, _, event = add_friendship_points(
                personality, "positive_feedback", db
            )
            result["points_awarded"].append({
                "activity": "positive_feedback",
                "points": event["points_earned"]
            })
            result["activities_detected"].append("positive_feedback")

        return result

    def on_conversation_end(
        self,
        conversation_id: int,
        personality: BotPersonality,
        db: Session
    ) -> Dict:
        """
        Handle conversation end event
        Awards points based on conversation quality

        Args:
            conversation_id: Conversation ID
            personality: BotPersonality object
            db: Database session

        Returns:
            Dictionary with points awarded and metrics
        """
        result = {
            "points_awarded": [],
            "conversation_quality": "short",
            "message_count": 0,
        }

        # Get conversation
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

        if not conversation:
            logger.warning(f"Conversation {conversation_id} not found")
            return result

        message_count = conversation.message_count or 0
        result["message_count"] = message_count

        # Award points for completing conversation
        _, _, event = add_friendship_points(
            personality, "conversation_completed", db
        )
        result["points_awarded"].append({
            "activity": "conversation_completed",
            "points": event["points_earned"]
        })

        # Award bonus points for quality conversations
        if message_count >= 20:
            result["conversation_quality"] = "quality"
            _, _, event = add_friendship_points(
                personality, "quality_conversation", db
            )
            result["points_awarded"].append({
                "activity": "quality_conversation",
                "points": event["points_earned"]
            })
        elif message_count >= 10:
            result["conversation_quality"] = "long"
            _, _, event = add_friendship_points(
                personality, "long_conversation", db
            )
            result["points_awarded"].append({
                "activity": "long_conversation",
                "points": event["points_earned"]
            })

        # Increment total conversations
        personality.total_conversations += 1
        db.commit()

        logger.info(
            f"Conversation {conversation_id} ended: "
            f"{message_count} messages, quality: {result['conversation_quality']}"
        )

        return result

    def is_first_conversation_today(self, user_id: int, db: Session) -> bool:
        """
        Check if this is the first conversation today

        Args:
            user_id: User ID
            db: Database session

        Returns:
            True if first conversation today
        """
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        conversation_today = (
            db.query(Conversation)
            .filter(
                Conversation.user_id == user_id,
                Conversation.timestamp >= today_start
            )
            .first()
        )

        return conversation_today is None

    def calculate_streak(self, user_id: int, db: Session) -> int:
        """
        Calculate consecutive days streak

        Args:
            user_id: User ID
            db: Database session

        Returns:
            Number of consecutive days with conversations
        """
        # Get all conversation dates (distinct days)
        conversations = (
            db.query(
                func.date(Conversation.timestamp).label('date')
            )
            .filter(Conversation.user_id == user_id)
            .group_by(func.date(Conversation.timestamp))
            .order_by(func.date(Conversation.timestamp).desc())
            .all()
        )

        if not conversations:
            return 0

        # Convert to date objects
        dates = [conv.date for conv in conversations]

        # Check for streak starting from today
        today = datetime.now().date()
        streak = 0

        # Check if there was a conversation today
        if dates[0] == today:
            streak = 1
        # If no conversation today, check yesterday (ongoing streak)
        elif dates[0] == today - timedelta(days=1):
            streak = 1
        else:
            # No recent activity, streak is 0
            return 0

        # Count consecutive days backwards
        expected_date = dates[0] - timedelta(days=1)

        for i in range(1, len(dates)):
            if dates[i] == expected_date:
                streak += 1
                expected_date -= timedelta(days=1)
            else:
                # Gap in dates, streak ends
                break

        return streak

    def get_conversation_stats(self, user_id: int, db: Session) -> Dict:
        """
        Get conversation statistics for a user

        Args:
            user_id: User ID
            db: Database session

        Returns:
            Dictionary with conversation stats
        """
        # Get total conversations
        total_conversations = (
            db.query(func.count(Conversation.id))
            .filter(Conversation.user_id == user_id)
            .scalar()
        ) or 0

        # Get total messages
        total_messages = (
            db.query(func.count(Message.id))
            .join(Conversation)
            .filter(Conversation.user_id == user_id)
            .scalar()
        ) or 0

        # Get average messages per conversation
        avg_messages = (
            db.query(func.avg(Conversation.message_count))
            .filter(
                Conversation.user_id == user_id,
                Conversation.message_count.isnot(None)
            )
            .scalar()
        ) or 0

        # Get average duration
        avg_duration = (
            db.query(func.avg(Conversation.duration_seconds))
            .filter(
                Conversation.user_id == user_id,
                Conversation.duration_seconds.isnot(None)
            )
            .scalar()
        ) or 0

        # Get first and last conversation dates
        first_conversation = (
            db.query(Conversation)
            .filter(Conversation.user_id == user_id)
            .order_by(Conversation.timestamp.asc())
            .first()
        )

        last_conversation = (
            db.query(Conversation)
            .filter(Conversation.user_id == user_id)
            .order_by(Conversation.timestamp.desc())
            .first()
        )

        # Calculate days active
        if first_conversation:
            days_active = (datetime.now() - first_conversation.timestamp).days + 1
        else:
            days_active = 0

        # Get current streak
        current_streak = self.calculate_streak(user_id, db)

        # Get conversations this week
        week_ago = datetime.now() - timedelta(days=7)
        conversations_this_week = (
            db.query(func.count(Conversation.id))
            .filter(
                Conversation.user_id == user_id,
                Conversation.timestamp >= week_ago
            )
            .scalar()
        ) or 0

        # Get conversations this month
        month_ago = datetime.now() - timedelta(days=30)
        conversations_this_month = (
            db.query(func.count(Conversation.id))
            .filter(
                Conversation.user_id == user_id,
                Conversation.timestamp >= month_ago
            )
            .scalar()
        ) or 0

        return {
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "avg_messages_per_conversation": round(float(avg_messages), 1),
            "avg_duration_seconds": round(float(avg_duration), 1),
            "days_active": days_active,
            "current_streak": current_streak,
            "conversations_this_week": conversations_this_week,
            "conversations_this_month": conversations_this_month,
            "first_conversation": (
                first_conversation.timestamp.isoformat()
                if first_conversation else None
            ),
            "last_conversation": (
                last_conversation.timestamp.isoformat()
                if last_conversation else None
            ),
        }

    def get_recent_conversations(
        self,
        user_id: int,
        db: Session,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get recent conversations with basic info

        Args:
            user_id: User ID
            db: Database session
            limit: Maximum number of conversations to return

        Returns:
            List of conversation dictionaries
        """
        conversations = (
            db.query(Conversation)
            .filter(Conversation.user_id == user_id)
            .order_by(Conversation.timestamp.desc())
            .limit(limit)
            .all()
        )

        return [conv.to_dict(include_messages=False) for conv in conversations]

    def get_longest_streak(self, user_id: int, db: Session) -> int:
        """
        Calculate the longest streak ever achieved

        Args:
            user_id: User ID
            db: Database session

        Returns:
            Longest streak in days
        """
        # Get all conversation dates
        conversations = (
            db.query(
                func.date(Conversation.timestamp).label('date')
            )
            .filter(Conversation.user_id == user_id)
            .group_by(func.date(Conversation.timestamp))
            .order_by(func.date(Conversation.timestamp).asc())
            .all()
        )

        if not conversations:
            return 0

        dates = [conv.date for conv in conversations]

        max_streak = 1
        current_streak = 1

        for i in range(1, len(dates)):
            if dates[i] == dates[i-1] + timedelta(days=1):
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 1

        return max_streak


# Global instance
conversation_tracker = ConversationTracker()


# Convenience functions
def on_conversation_start(
    user_id: int,
    personality: BotPersonality,
    db: Session
) -> Dict:
    """Handle conversation start event"""
    return conversation_tracker.on_conversation_start(user_id, personality, db)


def on_message_sent(
    user_id: int,
    personality: BotPersonality,
    message: str,
    db: Session
) -> Dict:
    """Handle message sent event"""
    return conversation_tracker.on_message_sent(user_id, personality, message, db)


def on_conversation_end(
    conversation_id: int,
    personality: BotPersonality,
    db: Session
) -> Dict:
    """Handle conversation end event"""
    return conversation_tracker.on_conversation_end(conversation_id, personality, db)


def get_conversation_stats(user_id: int, db: Session) -> Dict:
    """Get conversation statistics"""
    return conversation_tracker.get_conversation_stats(user_id, db)
