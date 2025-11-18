"""
Template Personalization Service
Personalizes advice templates with user data and context

This service extracts user context and intelligently fills template
placeholders to make advice more personal and relevant.
"""

from typing import Dict, List, Optional, Any
import logging
import re

from sqlalchemy.orm import Session
from models.user import User
from models.personality import BotPersonality
from models.conversation import Message
from models.safety import AdviceTemplate

logger = logging.getLogger("chatbot.template_personalization")


class TemplatePersonalizationService:
    """
    Template Personalization Service - personalizes advice templates with user data

    Features:
    - Extract user context from database (name, age, interests, etc.)
    - Extract conversation context (recent topics, detected entities)
    - Intelligently fill template placeholders
    - Handle missing data gracefully with defaults
    - Extract entities from user messages (friend names, situations, etc.)
    - Support multiple placeholder formats

    Supported Placeholders:
    - {name} - User's name
    - {friend_name} - Friend's name (extracted from context)
    - {bot_name} - Bot's name
    - {age} - User's age
    - {situation} - Described situation (extracted from context)
    - {topic} - Topic being discussed
    - {feeling} - User's feeling/emotion
    - {activity} - Activity mentioned
    """

    def __init__(self):
        """Initialize TemplatePersonalizationService"""
        self.templates_personalized = 0
        logger.info("TemplatePersonalizationService initialized")

    def personalize_template(
        self,
        template: AdviceTemplate,
        db: Session,
        user_id: int,
        user_message: Optional[str] = None,
        detected_mood: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Personalize advice template with user data

        Args:
            template: AdviceTemplate to personalize
            db: Database session
            user_id: User ID
            user_message: User's original message (for context extraction)
            detected_mood: Detected user mood
            additional_context: Additional context variables

        Returns:
            Personalized advice string
        """
        # Extract user context
        user_context = self._extract_user_context(db, user_id)

        # Extract message context if available
        message_context = {}
        if user_message:
            message_context = self._extract_message_context(user_message, detected_mood)

        # Merge contexts
        context_vars = {**user_context, **message_context}

        # Add additional context if provided
        if additional_context:
            context_vars.update(additional_context)

        # Format template
        personalized = template.format_advice(**context_vars)

        # Post-process to clean up any remaining placeholders
        personalized = self._clean_remaining_placeholders(personalized, context_vars)

        self.templates_personalized += 1

        logger.info(
            f"Personalized template {template.id} for user {user_id}, "
            f"filled {len(context_vars)} variables"
        )

        return personalized

    def _extract_user_context(self, db: Session, user_id: int) -> Dict[str, Any]:
        """
        Extract user context from database

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Dictionary with user context variables
        """
        context = {}

        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            context["name"] = user.name or "friend"
            context["user_name"] = user.name or "friend"

        # Get bot personality
        personality = db.query(BotPersonality).filter(BotPersonality.user_id == user_id).first()
        if personality:
            context["bot_name"] = personality.name or "ChessBot"
            context["friendship_level"] = personality.friendship_level
            context["mood"] = personality.mood

            # Extract interests if available
            interests = personality.get_interests()
            if interests:
                context["interests"] = ", ".join(interests[:3])
                context["interest"] = interests[0] if interests else "hobbies"

            # Extract quirks if available
            quirks = personality.get_quirks()
            if quirks:
                context["quirks"] = ", ".join(quirks)

        # Default values if not found
        context.setdefault("name", "friend")
        context.setdefault("user_name", "friend")
        context.setdefault("bot_name", "ChessBot")

        return context

    def _extract_message_context(
        self, user_message: str, detected_mood: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract context from user's message

        Args:
            user_message: User's message
            detected_mood: Detected user mood

        Returns:
            Dictionary with message context variables
        """
        context = {}

        # Add detected mood/feeling
        if detected_mood:
            context["feeling"] = detected_mood
            context["emotion"] = detected_mood

        # Extract potential friend names (capitalized words after "my friend", "with", etc.)
        friend_names = self._extract_friend_names(user_message)
        if friend_names:
            context["friend_name"] = friend_names[0]
            if len(friend_names) > 1:
                context["friends"] = " and ".join(friend_names)

        # Extract activities (words after "doing", "playing", "studying", etc.)
        activities = self._extract_activities(user_message)
        if activities:
            context["activity"] = activities[0]

        # Extract subjects/topics (words after "about", "with", etc.)
        topics = self._extract_topics(user_message)
        if topics:
            context["topic"] = topics[0]
            context["subject"] = topics[0]

        # Extract situations (phrases describing problems/situations)
        situation = self._extract_situation(user_message)
        if situation:
            context["situation"] = situation

        return context

    def _extract_friend_names(self, message: str) -> List[str]:
        """
        Extract potential friend names from message

        Args:
            message: User's message

        Returns:
            List of potential friend names
        """
        names = []

        # Patterns to detect friend names
        patterns = [
            r"(?:my friend|with|and)\s+([A-Z][a-z]+)",
            r"(?:named|called)\s+([A-Z][a-z]+)",
            r"([A-Z][a-z]+)\s+(?:is|was|said|told)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, message)
            names.extend(matches)

        # Remove common non-name words
        non_names = {"He", "She", "They", "My", "The", "This", "That", "We", "I"}
        names = [n for n in names if n not in non_names]

        # Deduplicate while preserving order
        seen = set()
        unique_names = []
        for name in names:
            if name not in seen:
                seen.add(name)
                unique_names.append(name)

        return unique_names[:2]  # Limit to 2 names

    def _extract_activities(self, message: str) -> List[str]:
        """
        Extract activities from message

        Args:
            message: User's message

        Returns:
            List of activities
        """
        activities = []

        # Patterns to detect activities
        patterns = [
            r"(?:playing|doing|practicing|studying|watching|reading|making)\s+(\w+)",
            r"(?:play|do|practice|study|watch|read|make)\s+(\w+)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, message.lower())
            activities.extend(matches)

        # Clean up common words
        stopwords = {"the", "a", "an", "my", "your", "about", "with", "for", "to", "on"}
        activities = [a for a in activities if a not in stopwords]

        return activities[:2]  # Limit to 2 activities

    def _extract_topics(self, message: str) -> List[str]:
        """
        Extract topics from message

        Args:
            message: User's message

        Returns:
            List of topics
        """
        topics = []

        # Patterns to detect topics
        patterns = [
            r"about\s+(\w+)",
            r"(?:homework|test|project|assignment|essay)(?:\s+in|\s+for)?\s+(\w+)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, message.lower())
            topics.extend(matches)

        # Filter out common words
        stopwords = {"the", "a", "an", "my", "your", "this", "that", "it"}
        topics = [t for t in topics if t not in stopwords and len(t) > 2]

        return topics[:2]  # Limit to 2 topics

    def _extract_situation(self, message: str) -> Optional[str]:
        """
        Extract situation description from message

        Args:
            message: User's message

        Returns:
            Situation description or None
        """
        # Look for common problem/situation patterns
        situation_markers = [
            r"(?:I have|I'm having|I got)\s+(a\s+)?(.+?)(?:\.|$|\?)",
            r"(?:problem with|trouble with|issue with)\s+(.+?)(?:\.|$|\?)",
        ]

        for pattern in situation_markers:
            match = re.search(pattern, message.lower())
            if match:
                # Get the last capturing group
                situation = match.group(match.lastindex)
                # Clean up
                situation = situation.strip()
                if len(situation) > 5 and len(situation) < 50:
                    return situation

        return None

    def _clean_remaining_placeholders(
        self, text: str, filled_context: Dict[str, Any]
    ) -> str:
        """
        Clean up any remaining placeholders that weren't filled

        Args:
            text: Text with potential unfilled placeholders
            filled_context: Context variables that were filled

        Returns:
            Cleaned text
        """
        # Find all placeholders still in text
        placeholders = re.findall(r"\{(\w+)\}", text)

        for placeholder in placeholders:
            # If we don't have this variable, try to provide a reasonable default
            if placeholder not in filled_context:
                default_value = self._get_default_placeholder_value(placeholder)
                if default_value:
                    text = text.replace(f"{{{placeholder}}}", default_value)
                else:
                    # Remove the placeholder and clean up grammar
                    text = self._remove_placeholder_gracefully(text, placeholder)

        return text

    def _get_default_placeholder_value(self, placeholder: str) -> Optional[str]:
        """
        Get default value for a placeholder

        Args:
            placeholder: Placeholder name

        Returns:
            Default value or None
        """
        defaults = {
            "name": "friend",
            "user_name": "friend",
            "bot_name": "me",
            "friend_name": "your friend",
            "friends": "your friends",
            "feeling": "this way",
            "emotion": "this way",
            "activity": "that",
            "topic": "this",
            "subject": "this",
            "situation": "this situation",
        }

        return defaults.get(placeholder)

    def _remove_placeholder_gracefully(self, text: str, placeholder: str) -> str:
        """
        Remove placeholder and clean up surrounding text

        Args:
            text: Text containing placeholder
            placeholder: Placeholder to remove

        Returns:
            Cleaned text
        """
        # Pattern to match placeholder with surrounding context
        placeholder_pattern = f"\\{{{placeholder}\\}}"

        # Try to remove placeholder and clean up grammar
        # Remove "with {placeholder}" → ""
        text = re.sub(f"\\s+with\\s+{placeholder_pattern}", "", text)

        # Remove "{placeholder} and" → ""
        text = re.sub(f"{placeholder_pattern}\\s+and\\s+", "", text)

        # Remove "and {placeholder}" → ""
        text = re.sub(f"\\s+and\\s+{placeholder_pattern}", "", text)

        # Remove remaining placeholder
        text = text.replace(f"{{{placeholder}}}", "")

        # Clean up double spaces
        text = re.sub(r"\s+", " ", text)

        # Clean up punctuation issues
        text = re.sub(r"\s+([.,!?])", r"\1", text)

        return text.strip()

    def get_placeholder_requirements(self, template: AdviceTemplate) -> List[str]:
        """
        Get list of placeholders required by a template

        Args:
            template: AdviceTemplate to analyze

        Returns:
            List of placeholder names
        """
        placeholders = re.findall(r"\{(\w+)\}", template.template)
        return list(set(placeholders))

    def can_fill_template(
        self,
        template: AdviceTemplate,
        available_context: Dict[str, Any]
    ) -> bool:
        """
        Check if we have enough context to fill template

        Args:
            template: AdviceTemplate to check
            available_context: Available context variables

        Returns:
            True if we can reasonably fill the template
        """
        required = self.get_placeholder_requirements(template)

        # Check if we have values or defaults for all placeholders
        for placeholder in required:
            if placeholder not in available_context:
                # Check if we have a default
                if not self._get_default_placeholder_value(placeholder):
                    return False

        return True

    def get_stats(self) -> Dict:
        """
        Get service statistics

        Returns:
            Dictionary with service stats
        """
        return {
            "templates_personalized": self.templates_personalized,
            "service_status": "active",
        }


# Global instance
template_personalization_service = TemplatePersonalizationService()


# Convenience functions
def personalize_template(
    template: AdviceTemplate,
    db: Session,
    user_id: int,
    user_message: Optional[str] = None,
    detected_mood: Optional[str] = None,
    additional_context: Optional[Dict[str, Any]] = None
) -> str:
    """Personalize advice template"""
    return template_personalization_service.personalize_template(
        template, db, user_id, user_message, detected_mood, additional_context
    )


def get_placeholder_requirements(template: AdviceTemplate) -> List[str]:
    """Get placeholder requirements"""
    return template_personalization_service.get_placeholder_requirements(template)


def can_fill_template(
    template: AdviceTemplate,
    available_context: Dict[str, Any]
) -> bool:
    """Check if template can be filled"""
    return template_personalization_service.can_fill_template(template, available_context)


def get_stats() -> Dict:
    """Get service statistics"""
    return template_personalization_service.get_stats()
