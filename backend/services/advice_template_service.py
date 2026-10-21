"""
Advice Template Service
Retrieves and manages advice templates based on category and friendship level

This service handles selecting appropriate advice templates from the database
based on detected advice categories, user friendship level, age, and other factors.
"""

from typing import Dict, List, Optional, Tuple
import logging
import math
import random
import re

from sqlalchemy.orm import Session
from models.safety import AdviceTemplate
from models.personality import BotPersonality
from services.template_personalization_service import template_personalization_service

logger = logging.getLogger("chatbot.advice_template_service")

# A template is used for a message only if its matched keywords weigh at least this much.
# A keyword's weight is log(templates / templates with that keyword): "friend" (in about
# 10 of 56 templates) weighs 1.7, so it is not enough on its own; "recital" (in one) weighs 4.0
RELEVANCE_THRESHOLD = 2.5


class AdviceTemplateService:
    """
    Advice Template Service - retrieves and selects appropriate advice templates

    Features:
    - Retrieve templates by category and friendship level
    - Filter by age appropriateness
    - Select best template based on multiple criteria
    - Format templates with user context
    - Track template usage
    - Support for expert-reviewed templates

    Selection Strategies:
    - random: Random selection from available templates
    - most_used: Select most frequently used template
    - expert_reviewed: Prefer expert-reviewed templates
    - tone_match: Match template tone to user mood/context
    """

    def __init__(self):
        """Initialize AdviceTemplateService"""
        self.templates_retrieved = 0
        self.templates_used = 0
        logger.info("AdviceTemplateService initialized")

    def get_advice_template(
        self,
        db: Session,
        category: str,
        friendship_level: int,
        age: Optional[int] = None,
        subcategory: Optional[str] = None,
        tone: Optional[str] = None,
        strategy: str = "expert_reviewed"
    ) -> Optional[AdviceTemplate]:
        """
        Get the best advice template for given criteria

        Args:
            db: Database session
            category: Advice category (friendship, school, etc.)
            friendship_level: Current friendship level (1-10)
            age: User's age (optional)
            subcategory: Optional subcategory filter
            tone: Preferred tone (optional)
            strategy: Selection strategy (random, most_used, expert_reviewed, tone_match)

        Returns:
            Selected AdviceTemplate or None if no templates found
        """
        # Get available templates
        templates = self._get_available_templates(
            db=db,
            category=category,
            friendship_level=friendship_level,
            age=age,
            subcategory=subcategory,
            tone=tone
        )

        if not templates:
            logger.warning(
                f"No templates found for category={category}, "
                f"friendship_level={friendship_level}, age={age}"
            )
            return None

        self.templates_retrieved += len(templates)

        # Select best template based on strategy
        selected = self._select_template(templates, strategy, tone)

        if selected:
            self.templates_used += 1
            logger.info(
                f"Selected template {selected.id} for category={category}, "
                f"strategy={strategy}"
            )

        return selected

    def get_formatted_advice(
        self,
        db: Session,
        category: str,
        friendship_level: int,
        user_id: Optional[int] = None,
        user_message: Optional[str] = None,
        detected_mood: Optional[str] = None,
        age: Optional[int] = None,
        subcategory: Optional[str] = None,
        tone: Optional[str] = None,
        strategy: str = "expert_reviewed",
        **format_kwargs
    ) -> Optional[str]:
        """
        Get formatted advice text ready to use with personalization

        Args:
            db: Database session
            category: Advice category
            friendship_level: Current friendship level
            user_id: User ID for personalization (optional)
            user_message: User's message for context extraction (optional)
            detected_mood: Detected user mood (optional)
            age: User's age
            subcategory: Optional subcategory filter
            tone: Preferred tone
            strategy: Selection strategy
            **format_kwargs: Additional variables for template formatting

        Returns:
            Formatted advice string or None if no template found
        """
        # Get template: the one that matches what the child said, if the message is given
        if user_message:
            template = self.find_relevant_template(
                db=db,
                user_message=user_message,
                friendship_level=friendship_level,
                age=age,
                category=category,
                tone=tone,
            )
        else:
            template = self.get_advice_template(
                db=db,
                category=category,
                friendship_level=friendship_level,
                age=age,
                subcategory=subcategory,
                tone=tone,
                strategy=strategy
            )

        if not template:
            return None

        # Use personalization service if user_id provided
        if user_id:
            formatted = template_personalization_service.personalize_template(
                template=template,
                db=db,
                user_id=user_id,
                user_message=user_message,
                detected_mood=detected_mood,
                additional_context=format_kwargs
            )
        else:
            # Fall back to basic formatting; templates use {name} for the user's name
            format_kwargs.setdefault("name", format_kwargs.pop("user_name", None) or "friend")
            formatted = template.format_advice(**format_kwargs)

        # Increment usage count
        template.increment_usage()
        db.commit()

        return formatted

    def find_relevant_template(
        self,
        db: Session,
        user_message: str,
        friendship_level: int,
        age: Optional[int] = None,
        category: Optional[str] = None,
        tone: Optional[str] = None,
    ) -> Optional[AdviceTemplate]:
        """
        The available template whose keywords best match the child's message

        Templates from every category are considered (the detector's categories do not line
        up with the templates': a test is "school", its templates are "school_stress" and
        "emotional"). Each matched keyword adds its weight (rarer keywords weigh more); the
        detected category, then the preferred tone, then expert review break ties.

        Args:
            db: Database session
            user_message: The child's message
            friendship_level: Current friendship level (templates above it are not used)
            age: User's age (templates for other ages are not used)
            category: Detected advice category, used to break ties
            tone: Preferred tone, used to break ties

        Returns:
            The best matching template, or None if none reaches RELEVANCE_THRESHOLD
        """
        all_templates = db.query(AdviceTemplate).all()
        if not all_templates:
            return None

        # Keyword weights from how many templates use each keyword
        counts: Dict[str, int] = {}
        for template in all_templates:
            for keyword in {k.lower() for k in template.get_keywords()}:
                counts[keyword] = counts.get(keyword, 0) + 1
        weights = {k: math.log(len(all_templates) / n) for k, n in counts.items()}

        text = user_message.lower()
        scored = []
        for template in all_templates:
            if template.min_friendship_level > friendship_level:
                continue
            if template.max_friendship_level is not None and template.max_friendship_level < friendship_level:
                continue
            if age and not (template.min_age <= age <= template.max_age):
                continue
            score = sum(weights[k] for k in {k.lower() for k in template.get_keywords()}
                        if self._mentions(text, k))
            if score >= RELEVANCE_THRESHOLD:
                in_category = bool(category) and template.category.startswith(category)
                scored.append((score, in_category, template.tone == tone, template.expert_reviewed,
                               random.random(), template))

        if not scored:
            return None
        best = max(scored, key=lambda entry: entry[:5])[-1]
        self.templates_used += 1
        logger.info(f"Selected template {best.id} ({best.category}) for the message")
        return best

    @staticmethod
    def _mentions(text: str, keyword: str) -> bool:
        """The keyword or phrase as whole words, also with an ending ("fight" in "fighting")"""
        return re.search(rf"\b{re.escape(keyword)}(?:s|es|d|ed|ing)?\b", text) is not None

    def get_multiple_advice_options(
        self,
        db: Session,
        category: str,
        friendship_level: int,
        age: Optional[int] = None,
        limit: int = 3
    ) -> List[AdviceTemplate]:
        """
        Get multiple advice template options for variety

        Args:
            db: Database session
            category: Advice category
            friendship_level: Current friendship level
            age: User's age
            limit: Maximum number of templates to return

        Returns:
            List of AdviceTemplate objects
        """
        templates = self._get_available_templates(
            db=db,
            category=category,
            friendship_level=friendship_level,
            age=age
        )

        # Return up to limit templates
        if len(templates) <= limit:
            return templates

        # Prefer expert-reviewed templates
        expert_reviewed = [t for t in templates if t.expert_reviewed]
        if len(expert_reviewed) >= limit:
            return random.sample(expert_reviewed, limit)

        # Mix expert-reviewed and others
        result = expert_reviewed.copy()
        remaining = [t for t in templates if not t.expert_reviewed]
        needed = limit - len(result)
        if needed > 0 and remaining:
            result.extend(random.sample(remaining, min(needed, len(remaining))))

        return result[:limit]

    def _get_available_templates(
        self,
        db: Session,
        category: str,
        friendship_level: int,
        age: Optional[int] = None,
        subcategory: Optional[str] = None,
        tone: Optional[str] = None
    ) -> List[AdviceTemplate]:
        """
        Get all available templates matching criteria

        Args:
            db: Database session
            category: Advice category
            friendship_level: Current friendship level
            age: User's age (optional)
            subcategory: Optional subcategory filter
            tone: Optional tone filter

        Returns:
            List of available AdviceTemplate objects
        """
        # Get templates by category
        templates = AdviceTemplate.get_by_category(
            db=db,
            category=category,
            friendship_level=friendship_level,
            age=age,
            subcategory=subcategory
        )

        # Additional tone filtering if specified; keep all templates if none match the tone
        if tone:
            tone_matches = [t for t in templates if t.tone == tone or t.tone is None]
            templates = tone_matches or templates

        return templates

    def _select_template(
        self,
        templates: List[AdviceTemplate],
        strategy: str,
        preferred_tone: Optional[str] = None
    ) -> Optional[AdviceTemplate]:
        """
        Select best template from available templates using strategy

        Args:
            templates: List of available templates
            strategy: Selection strategy
            preferred_tone: Preferred tone (for tone_match strategy)

        Returns:
            Selected AdviceTemplate or None
        """
        if not templates:
            return None

        if strategy == "random":
            return random.choice(templates)

        elif strategy == "most_used":
            # Select most frequently used
            return max(templates, key=lambda t: t.usage_count)

        elif strategy == "expert_reviewed":
            # Prefer expert-reviewed templates
            expert_reviewed = [t for t in templates if t.expert_reviewed]
            if expert_reviewed:
                return random.choice(expert_reviewed)
            return random.choice(templates)

        elif strategy == "tone_match":
            # Match tone if possible
            if preferred_tone:
                tone_match = [t for t in templates if t.tone == preferred_tone]
                if tone_match:
                    return random.choice(tone_match)

            # Fall back to expert-reviewed
            expert_reviewed = [t for t in templates if t.expert_reviewed]
            if expert_reviewed:
                return random.choice(expert_reviewed)
            return random.choice(templates)

        else:
            # Default: prefer expert-reviewed, then random
            expert_reviewed = [t for t in templates if t.expert_reviewed]
            if expert_reviewed:
                return random.choice(expert_reviewed)
            return random.choice(templates)

    def get_template_by_id(self, db: Session, template_id: int) -> Optional[AdviceTemplate]:
        """
        Get specific template by ID

        Args:
            db: Database session
            template_id: Template ID

        Returns:
            AdviceTemplate or None
        """
        return db.query(AdviceTemplate).filter(AdviceTemplate.id == template_id).first()

    def get_advice_for_context(
        self,
        db: Session,
        advice_detection: Dict,
        personality: BotPersonality,
        user_id: Optional[int] = None,
        user_message: Optional[str] = None,
        user_age: Optional[int] = None,
        detected_mood: Optional[str] = None,
        user_name: Optional[str] = None
    ) -> Optional[str]:
        """
        Get advice based on full conversation context with personalization

        Args:
            db: Database session
            advice_detection: Result from AdviceCategoryDetector
            personality: User's bot personality
            user_id: User ID for personalization
            user_message: User's original message for context extraction
            user_age: User's age
            detected_mood: Detected user mood
            user_name: User's name, used when no user_id is available for personalization

        Returns:
            Formatted and personalized advice string or None
        """
        if not advice_detection.get("is_advice_request"):
            return None

        category = advice_detection.get("category", "general")
        confidence = advice_detection.get("confidence", 0.0)

        # Don't provide template advice for low confidence
        if confidence < 0.5:
            return None

        # Map mood to tone
        tone_mapping = {
            "sad": "empathetic",
            "anxious": "supportive",
            "happy": "encouraging",
            "angry": "supportive",
            "neutral": "practical"
        }
        preferred_tone = tone_mapping.get(detected_mood, "supportive")

        # Get formatted advice with personalization
        advice = self.get_formatted_advice(
            db=db,
            category=category,
            friendship_level=personality.friendship_level,
            user_id=user_id,
            user_message=user_message,
            detected_mood=detected_mood,
            age=user_age,
            tone=preferred_tone,
            strategy="tone_match",
            **({"user_name": user_name} if user_name else {})
        )

        return advice

    def get_stats(self) -> Dict:
        """
        Get service statistics

        Returns:
            Dictionary with service stats
        """
        return {
            "templates_retrieved": self.templates_retrieved,
            "templates_used": self.templates_used,
            "service_status": "active",
        }


# Global instance
advice_template_service = AdviceTemplateService()


# Convenience functions
def get_advice_template(
    db: Session,
    category: str,
    friendship_level: int,
    age: Optional[int] = None,
    subcategory: Optional[str] = None,
    tone: Optional[str] = None,
    strategy: str = "expert_reviewed"
) -> Optional[AdviceTemplate]:
    """Get advice template"""
    return advice_template_service.get_advice_template(
        db, category, friendship_level, age, subcategory, tone, strategy
    )


def get_formatted_advice(
    db: Session,
    category: str,
    friendship_level: int,
    user_id: Optional[int] = None,
    user_message: Optional[str] = None,
    detected_mood: Optional[str] = None,
    age: Optional[int] = None,
    subcategory: Optional[str] = None,
    tone: Optional[str] = None,
    strategy: str = "expert_reviewed",
    **format_kwargs
) -> Optional[str]:
    """Get formatted advice with personalization"""
    return advice_template_service.get_formatted_advice(
        db, category, friendship_level, user_id, user_message, detected_mood,
        age, subcategory, tone, strategy, **format_kwargs
    )


def get_advice_for_context(
    db: Session,
    advice_detection: Dict,
    personality: BotPersonality,
    user_id: Optional[int] = None,
    user_message: Optional[str] = None,
    user_age: Optional[int] = None,
    detected_mood: Optional[str] = None,
    user_name: Optional[str] = None
) -> Optional[str]:
    """Get advice for full context with personalization"""
    return advice_template_service.get_advice_for_context(
        db, advice_detection, personality, user_id, user_message, user_age, detected_mood,
        user_name
    )


def get_stats() -> Dict:
    """Get service statistics"""
    return advice_template_service.get_stats()
