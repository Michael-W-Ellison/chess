"""
Personality Drift Calculator Service
Calculates personality trait changes based on conversation metrics
"""

from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import func
from models.personality import BotPersonality
from models.personality_drift import PersonalityDrift
from models.conversation import Conversation, Message
from services.drift_rate_limiter import drift_rate_limiter

logger = logging.getLogger("chatbot.personality_drift")


class PersonalityDriftCalculator:
    """
    Personality Drift Calculator - adjusts personality traits based on conversation patterns

    Drift Rules:
    - Humor: Increases when user laughs, decreases with serious topics
    - Energy: Increases with active conversations, decreases with short sessions
    - Curiosity: Increases when user shares, decreases with one-word answers
    - Formality: Decreases with casual language, increases with formal topics

    All traits are bounded [0.0, 1.0] and change gradually (0.01-0.05 per conversation)
    """

    # Drift configuration
    DRIFT_AMOUNT_SMALL = 0.01   # Minor adjustment
    DRIFT_AMOUNT_MEDIUM = 0.03  # Moderate adjustment
    DRIFT_AMOUNT_LARGE = 0.05   # Significant adjustment

    # Trait bounds
    TRAIT_MIN = 0.0
    TRAIT_MAX = 1.0

    # Thresholds for conversation analysis
    LONG_CONVERSATION_THRESHOLD = 10  # messages
    QUALITY_CONVERSATION_THRESHOLD = 20  # messages
    SHORT_MESSAGE_THRESHOLD = 10  # characters

    def __init__(self):
        """Initialize the drift calculator"""
        pass

    def calculate_drift_after_conversation(
        self,
        personality: BotPersonality,
        conversation: Conversation,
        db: Session
    ) -> List[PersonalityDrift]:
        """
        Calculate personality drift after a conversation completes

        Args:
            personality: BotPersonality object
            conversation: Conversation object
            db: Database session

        Returns:
            List of PersonalityDrift objects created
        """
        drift_events = []

        # Analyze conversation
        analysis = self._analyze_conversation(conversation, db)

        # Calculate drift for each trait
        humor_drift = self._calculate_humor_drift(personality, analysis)
        energy_drift = self._calculate_energy_drift(personality, analysis)
        curiosity_drift = self._calculate_curiosity_drift(personality, analysis)
        formality_drift = self._calculate_formality_drift(personality, analysis)

        # Apply drifts and create events
        if humor_drift != 0:
            event = self._apply_drift(
                personality, "humor", humor_drift,
                "conversation_pattern", analysis["humor_reasons"],
                conversation.id, db
            )
            drift_events.append(event)

        if energy_drift != 0:
            event = self._apply_drift(
                personality, "energy", energy_drift,
                "conversation_pattern", analysis["energy_reasons"],
                conversation.id, db
            )
            drift_events.append(event)

        if curiosity_drift != 0:
            event = self._apply_drift(
                personality, "curiosity", curiosity_drift,
                "conversation_pattern", analysis["curiosity_reasons"],
                conversation.id, db
            )
            drift_events.append(event)

        if formality_drift != 0:
            event = self._apply_drift(
                personality, "formality", formality_drift,
                "conversation_pattern", analysis["formality_reasons"],
                conversation.id, db
            )
            drift_events.append(event)

        # Commit all changes
        db.commit()

        if drift_events:
            logger.info(
                f"Applied {len(drift_events)} personality drifts for user {personality.user_id} "
                f"after conversation {conversation.id}"
            )

        return drift_events

    def _analyze_conversation(
        self,
        conversation: Conversation,
        db: Session
    ) -> Dict:
        """
        Analyze a conversation for drift triggers

        Args:
            conversation: Conversation object
            db: Database session

        Returns:
            Dictionary with analysis results
        """
        analysis = {
            "message_count": conversation.message_count or 0,
            "duration_seconds": conversation.duration_seconds or 0,
            "user_messages": [],
            "laughter_count": 0,
            "thanks_count": 0,
            "feelings_count": 0,
            "questions_count": 0,
            "short_messages_count": 0,
            "casual_language_count": 0,
            "formal_language_count": 0,
            "deep_topics_count": 0,
            "humor_reasons": [],
            "energy_reasons": [],
            "curiosity_reasons": [],
            "formality_reasons": [],
        }

        # Get user messages from conversation
        user_messages = (
            db.query(Message)
            .filter(
                Message.conversation_id == conversation.id,
                Message.role == "user"
            )
            .all()
        )

        analysis["user_messages"] = user_messages

        # Analyze each user message
        for msg in user_messages:
            content_lower = msg.content.lower()

            # Laughter detection
            if any(word in content_lower for word in ["lol", "haha", "hehe", "funny", "😂", "hilarious"]):
                analysis["laughter_count"] += 1

            # Gratitude detection
            if any(word in content_lower for word in ["thank", "thanks", "thx", "ty", "appreciate"]):
                analysis["thanks_count"] += 1

            # Feelings sharing
            feeling_words = [
                "feel", "feeling", "sad", "happy", "excited", "worried",
                "anxious", "scared", "nervous", "proud", "angry", "upset"
            ]
            if any(word in content_lower for word in feeling_words):
                analysis["feelings_count"] += 1

            # Questions asked by user
            if "?" in msg.content:
                analysis["questions_count"] += 1

            # Short messages
            if len(msg.content.strip()) < self.SHORT_MESSAGE_THRESHOLD:
                analysis["short_messages_count"] += 1

            # Casual language
            casual_words = ["yeah", "yep", "nah", "nope", "lol", "omg", "btw", "tbh", "idk"]
            if any(word in content_lower for word in casual_words):
                analysis["casual_language_count"] += 1

            # Formal language
            formal_indicators = ["however", "therefore", "furthermore", "consequently", "regarding"]
            if any(word in content_lower for word in formal_indicators):
                analysis["formal_language_count"] += 1

            # Deep topics
            deep_topics = [
                "life", "future", "dream", "goal", "worry", "fear",
                "meaning", "purpose", "philosophy", "death", "love"
            ]
            if any(topic in content_lower for topic in deep_topics):
                analysis["deep_topics_count"] += 1

        return analysis

    def _calculate_humor_drift(
        self,
        personality: BotPersonality,
        analysis: Dict
    ) -> float:
        """Calculate humor trait drift"""
        drift = 0.0
        reasons = []

        # User laughed a lot -> increase humor
        if analysis["laughter_count"] >= 3:
            drift += self.DRIFT_AMOUNT_MEDIUM
            reasons.append(f"User laughed {analysis['laughter_count']} times")
        elif analysis["laughter_count"] >= 1:
            drift += self.DRIFT_AMOUNT_SMALL
            reasons.append(f"User laughed {analysis['laughter_count']} time(s)")

        # Deep/serious topics -> decrease humor
        if analysis["deep_topics_count"] >= 3:
            drift -= self.DRIFT_AMOUNT_SMALL
            reasons.append(f"Discussed {analysis['deep_topics_count']} deep topics")

        # Feelings shared -> slight decrease in humor (user may need support)
        if analysis["feelings_count"] >= 3:
            drift -= self.DRIFT_AMOUNT_SMALL
            reasons.append(f"User shared feelings {analysis['feelings_count']} times")

        analysis["humor_reasons"] = reasons
        return drift

    def _calculate_energy_drift(
        self,
        personality: BotPersonality,
        analysis: Dict
    ) -> float:
        """Calculate energy trait drift"""
        drift = 0.0
        reasons = []

        # Long active conversation -> increase energy
        if analysis["message_count"] >= self.QUALITY_CONVERSATION_THRESHOLD:
            drift += self.DRIFT_AMOUNT_MEDIUM
            reasons.append(f"Quality conversation with {analysis['message_count']} messages")
        elif analysis["message_count"] >= self.LONG_CONVERSATION_THRESHOLD:
            drift += self.DRIFT_AMOUNT_SMALL
            reasons.append(f"Long conversation with {analysis['message_count']} messages")

        # Many short messages -> decrease energy (user not engaged)
        user_msg_count = len(analysis["user_messages"])
        if user_msg_count > 0:
            short_ratio = analysis["short_messages_count"] / user_msg_count
            if short_ratio > 0.7:  # More than 70% short messages
                drift -= self.DRIFT_AMOUNT_SMALL
                reasons.append(f"{int(short_ratio * 100)}% of messages were very short")

        # User showed enthusiasm (laughter, exclamation marks)
        if analysis["laughter_count"] >= 2:
            drift += self.DRIFT_AMOUNT_SMALL
            reasons.append("User showed enthusiasm")

        analysis["energy_reasons"] = reasons
        return drift

    def _calculate_curiosity_drift(
        self,
        personality: BotPersonality,
        analysis: Dict
    ) -> float:
        """Calculate curiosity trait drift"""
        drift = 0.0
        reasons = []

        # User asked questions -> increase curiosity (encourage engagement)
        if analysis["questions_count"] >= 3:
            drift += self.DRIFT_AMOUNT_MEDIUM
            reasons.append(f"User asked {analysis['questions_count']} questions")
        elif analysis["questions_count"] >= 1:
            drift += self.DRIFT_AMOUNT_SMALL
            reasons.append(f"User asked {analysis['questions_count']} question(s)")

        # User shared feelings -> increase curiosity (user trusts bot)
        if analysis["feelings_count"] >= 2:
            drift += self.DRIFT_AMOUNT_SMALL
            reasons.append(f"User shared feelings {analysis['feelings_count']} times")

        # Many short messages -> decrease curiosity (user not engaged)
        user_msg_count = len(analysis["user_messages"])
        if user_msg_count > 0:
            short_ratio = analysis["short_messages_count"] / user_msg_count
            if short_ratio > 0.7:
                drift -= self.DRIFT_AMOUNT_SMALL
                reasons.append("User gave mostly brief responses")

        analysis["curiosity_reasons"] = reasons
        return drift

    def _calculate_formality_drift(
        self,
        personality: BotPersonality,
        analysis: Dict
    ) -> float:
        """Calculate formality trait drift"""
        drift = 0.0
        reasons = []

        # Casual language -> decrease formality
        if analysis["casual_language_count"] >= 5:
            drift -= self.DRIFT_AMOUNT_MEDIUM
            reasons.append(f"User used casual language {analysis['casual_language_count']} times")
        elif analysis["casual_language_count"] >= 2:
            drift -= self.DRIFT_AMOUNT_SMALL
            reasons.append(f"User used casual language {analysis['casual_language_count']} times")

        # Formal language -> increase formality
        if analysis["formal_language_count"] >= 3:
            drift += self.DRIFT_AMOUNT_SMALL
            reasons.append(f"User used formal language {analysis['formal_language_count']} times")

        # Deep topics -> slight decrease in formality (more personal)
        if analysis["deep_topics_count"] >= 2:
            drift -= self.DRIFT_AMOUNT_SMALL
            reasons.append("Discussed personal/deep topics")

        # Feelings shared -> decrease formality (more intimate)
        if analysis["feelings_count"] >= 3:
            drift -= self.DRIFT_AMOUNT_SMALL
            reasons.append("User shared personal feelings")

        analysis["formality_reasons"] = reasons
        return drift

    def _apply_drift(
        self,
        personality: BotPersonality,
        trait_name: str,
        drift_amount: float,
        trigger_type: str,
        reasons: List[str],
        conversation_id: Optional[int],
        db: Session
    ) -> PersonalityDrift:
        """
        Apply a trait drift and create a drift event

        Args:
            personality: BotPersonality object
            trait_name: Name of trait to change
            drift_amount: Amount to change (can be negative)
            trigger_type: Type of trigger
            reasons: List of reasons for drift
            conversation_id: Optional conversation ID
            db: Database session

        Returns:
            PersonalityDrift object created
        """
        # Apply rate limits to drift amount
        rate_limited_drift, limit_messages = drift_rate_limiter.apply_rate_limits(
            personality,
            trait_name,
            drift_amount,
            db,
            conversation_id,
            enforce_cooldown=True
        )

        # Add rate limit messages to reasons
        if limit_messages:
            reasons = reasons + [f"Rate limit: {msg}" for msg in limit_messages]

        # Get current value
        old_value = getattr(personality, trait_name)

        # Calculate new value (bounded)
        new_value = old_value + rate_limited_drift
        new_value = max(self.TRAIT_MIN, min(self.TRAIT_MAX, new_value))

        # Calculate actual change (may be less if bounded)
        actual_change = new_value - old_value

        # Create drift event
        drift_event = PersonalityDrift(
            user_id=personality.user_id,
            trait_name=trait_name,
            old_value=old_value,
            new_value=new_value,
            change_amount=actual_change,
            trigger_type=trigger_type,
            conversation_id=conversation_id,
            friendship_level=personality.friendship_level,
        )

        # Set trigger details
        drift_event.set_trigger_details({
            "reasons": reasons,
            "requested_change": drift_amount,
            "rate_limited_change": rate_limited_drift,
            "actual_change": actual_change,
            "rate_limited": abs(rate_limited_drift) < abs(drift_amount),
            "bounded": abs(actual_change) < abs(rate_limited_drift),
            "limit_messages": limit_messages,
        })

        # Apply change to personality
        setattr(personality, trait_name, new_value)

        # Add to database
        db.add(drift_event)

        if abs(rate_limited_drift) < abs(drift_amount):
            logger.info(
                f"Rate limit applied: {trait_name} drift reduced from "
                f"{drift_amount:+.3f} to {rate_limited_drift:+.3f}"
            )

        logger.debug(
            f"Drift applied: {trait_name} {old_value:.3f} -> {new_value:.3f} "
            f"(change: {actual_change:+.3f})"
        )

        return drift_event

    def manual_trait_adjustment(
        self,
        personality: BotPersonality,
        trait_name: str,
        new_value: float,
        db: Session
    ) -> PersonalityDrift:
        """
        Manually adjust a trait (for user customization)

        Args:
            personality: BotPersonality object
            trait_name: Name of trait to change
            new_value: New value to set
            db: Database session

        Returns:
            PersonalityDrift object created
        """
        # Validate trait name
        valid_traits = ["humor", "energy", "curiosity", "formality"]
        if trait_name not in valid_traits:
            raise ValueError(f"Invalid trait name: {trait_name}")

        # Validate new value
        if not (self.TRAIT_MIN <= new_value <= self.TRAIT_MAX):
            raise ValueError(f"Trait value must be between {self.TRAIT_MIN} and {self.TRAIT_MAX}")

        # Get old value
        old_value = getattr(personality, trait_name)
        change = new_value - old_value

        # Create drift event
        drift_event = PersonalityDrift(
            user_id=personality.user_id,
            trait_name=trait_name,
            old_value=old_value,
            new_value=new_value,
            change_amount=change,
            trigger_type="manual",
            conversation_id=None,
            friendship_level=personality.friendship_level,
        )

        drift_event.set_trigger_details({
            "reasons": ["Manual adjustment by user"],
            "manual_adjustment": True,
        })

        # Apply change
        setattr(personality, trait_name, new_value)

        # Add to database
        db.add(drift_event)
        db.commit()

        logger.info(
            f"Manual trait adjustment: {trait_name} {old_value:.3f} -> {new_value:.3f} "
            f"for user {personality.user_id}"
        )

        return drift_event

    def get_drift_history(
        self,
        user_id: int,
        db: Session,
        trait_name: Optional[str] = None,
        limit: int = 50
    ) -> List[PersonalityDrift]:
        """
        Get drift history for a user

        Args:
            user_id: User ID
            db: Database session
            trait_name: Optional trait name to filter by
            limit: Maximum number of events to return

        Returns:
            List of PersonalityDrift objects
        """
        query = db.query(PersonalityDrift).filter(
            PersonalityDrift.user_id == user_id
        )

        if trait_name:
            query = query.filter(PersonalityDrift.trait_name == trait_name)

        drifts = (
            query
            .order_by(PersonalityDrift.timestamp.desc())
            .limit(limit)
            .all()
        )

        return drifts

    def get_drift_summary(
        self,
        user_id: int,
        db: Session
    ) -> Dict:
        """
        Get a summary of personality drift for a user

        Args:
            user_id: User ID
            db: Database session

        Returns:
            Dictionary with drift summary
        """
        # Get all drifts
        all_drifts = db.query(PersonalityDrift).filter(
            PersonalityDrift.user_id == user_id
        ).all()

        summary = {
            "total_drifts": len(all_drifts),
            "by_trait": {},
            "by_trigger": {},
            "recent_drifts": [],
        }

        # Analyze by trait
        for trait in ["humor", "energy", "curiosity", "formality"]:
            trait_drifts = [d for d in all_drifts if d.trait_name == trait]

            if trait_drifts:
                total_change = sum(d.change_amount for d in trait_drifts)
                avg_change = total_change / len(trait_drifts)

                summary["by_trait"][trait] = {
                    "drift_count": len(trait_drifts),
                    "total_change": round(total_change, 3),
                    "average_change": round(avg_change, 3),
                    "current_value": trait_drifts[0].new_value,
                    "original_value": trait_drifts[-1].old_value if trait_drifts else None,
                }

        # Analyze by trigger type
        trigger_types = set(d.trigger_type for d in all_drifts)
        for trigger in trigger_types:
            trigger_drifts = [d for d in all_drifts if d.trigger_type == trigger]
            summary["by_trigger"][trigger] = len(trigger_drifts)

        # Get recent drifts
        recent = (
            db.query(PersonalityDrift)
            .filter(PersonalityDrift.user_id == user_id)
            .order_by(PersonalityDrift.timestamp.desc())
            .limit(10)
            .all()
        )

        summary["recent_drifts"] = [d.to_dict() for d in recent]

        return summary

    def get_trait_timeline(
        self,
        user_id: int,
        trait_name: str,
        db: Session
    ) -> List[Dict]:
        """
        Get timeline of a specific trait's changes

        Args:
            user_id: User ID
            trait_name: Trait name
            db: Database session

        Returns:
            List of timeline points
        """
        drifts = (
            db.query(PersonalityDrift)
            .filter(
                PersonalityDrift.user_id == user_id,
                PersonalityDrift.trait_name == trait_name
            )
            .order_by(PersonalityDrift.timestamp.asc())
            .all()
        )

        timeline = []
        for drift in drifts:
            timeline.append({
                "timestamp": drift.timestamp.isoformat(),
                "value": drift.new_value,
                "change": drift.change_amount,
                "trigger": drift.trigger_type,
                "reasons": drift.get_trigger_details().get("reasons", []),
            })

        return timeline


# Global instance
personality_drift_calculator = PersonalityDriftCalculator()


# Convenience functions
def calculate_drift_after_conversation(
    personality: BotPersonality,
    conversation: Conversation,
    db: Session
) -> List[PersonalityDrift]:
    """Calculate personality drift after a conversation"""
    return personality_drift_calculator.calculate_drift_after_conversation(
        personality, conversation, db
    )


def manual_trait_adjustment(
    personality: BotPersonality,
    trait_name: str,
    new_value: float,
    db: Session
) -> PersonalityDrift:
    """Manually adjust a personality trait"""
    return personality_drift_calculator.manual_trait_adjustment(
        personality, trait_name, new_value, db
    )


def get_drift_summary(user_id: int, db: Session) -> Dict:
    """Get drift summary for a user"""
    return personality_drift_calculator.get_drift_summary(user_id, db)
