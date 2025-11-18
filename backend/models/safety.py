"""
Safety models
SafetyFlag for tracking safety events
AdviceTemplate for storing expert-reviewed advice
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import json

from database.database import Base


class SafetyFlag(Base):
    """
    SafetyFlag model - records safety events and concerns

    Tracks when potentially concerning content is detected:
    - Profanity
    - Crisis keywords (self-harm, suicide)
    - Bullying
    - Inappropriate requests

    Used for parent monitoring and system improvements.

    Relationships:
        - Many-to-one with User
        - Many-to-one with Message (optional)
    """

    __tablename__ = "safety_flags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=True)

    # Flag details
    flag_type = Column(String, nullable=False)      # 'profanity', 'crisis', 'bullying', 'inappropriate'
    severity = Column(String, nullable=False)       # 'low', 'medium', 'high', 'critical'
    content_snippet = Column(Text, nullable=True)   # First 100 chars of flagged content
    action_taken = Column(String, nullable=True)    # What the system did

    # Tracking
    timestamp = Column(DateTime, default=datetime.now, nullable=False)
    parent_notified = Column(Boolean, default=False, nullable=False)

    # Relationships
    user = relationship("User", back_populates="safety_flags")
    message = relationship("Message", back_populates="safety_flags")

    def __repr__(self):
        return f"<SafetyFlag(id={self.id}, type='{self.flag_type}', severity='{self.severity}')>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "message_id": self.message_id,
            "flag_type": self.flag_type,
            "severity": self.severity,
            "content_snippet": self.content_snippet,
            "action_taken": self.action_taken,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "parent_notified": self.parent_notified,
        }

    @classmethod
    def get_critical_flags(cls, db, user_id, since_date=None):
        """
        Get all critical severity flags for a user

        Args:
            db: Database session
            user_id: User ID
            since_date: Optional datetime to filter flags after this date

        Returns:
            List of SafetyFlag objects
        """
        query = db.query(cls).filter(
            cls.user_id == user_id,
            cls.severity == "critical"
        )

        if since_date:
            query = query.filter(cls.timestamp >= since_date)

        return query.order_by(cls.timestamp.desc()).all()


class AdviceTemplate(Base):
    """
    AdviceTemplate model - stores expert-reviewed advice templates

    Templates are used when the bot detects the user needs advice.
    Each template is tied to a category and has minimum friendship requirements.

    Categories (aligned with AdviceCategoryDetector):
        - friendship: Friend problems, making friends, peer relationships
        - school: Homework, teachers, grades, school activities
        - family: Parents, siblings, family relationships
        - emotional: Feelings, sadness, anxiety, worry, stress
        - hobby: Activities, interests, what to do for fun
        - bullying: Being bullied or witnessing bullying
        - social: Social situations, fitting in, social anxiety
        - decision: Making choices, deciding what to do
        - conflict: Arguments, disagreements, resolving conflicts
        - general: General life advice and guidance
    """

    __tablename__ = "advice_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Template details
    category = Column(String, nullable=False, index=True)        # Advice category
    subcategory = Column(String, nullable=True)                  # Optional subcategory for more specific filtering
    keywords = Column(Text, nullable=False)                      # JSON array of trigger keywords
    template = Column(Text, nullable=False)                      # Advice text with {placeholders}

    # Friendship and age requirements
    min_friendship_level = Column(Integer, default=1, nullable=False)
    max_friendship_level = Column(Integer, default=10, nullable=True)  # Optional max level
    min_age = Column(Integer, default=8, nullable=False)         # Minimum age appropriateness
    max_age = Column(Integer, default=14, nullable=False)        # Maximum age appropriateness

    # Quality and usage tracking
    expert_reviewed = Column(Boolean, default=False, nullable=False)
    usage_count = Column(Integer, default=0, nullable=False)     # How many times this template has been used
    rating = Column(Integer, default=0, nullable=True)           # Optional user rating (1-5)

    # Metadata
    tone = Column(String, nullable=True)                         # supportive, encouraging, empathetic, practical
    response_style = Column(String, nullable=True)               # direct, gentle, questioning, validating
    context_tags = Column(Text, nullable=True)                   # JSON array of additional context tags

    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=True)

    def get_keywords(self):
        """Parse keywords JSON array"""
        if self.keywords:
            try:
                return json.loads(self.keywords)
            except json.JSONDecodeError:
                return []
        return []

    def set_keywords(self, keywords_list):
        """Set keywords from list"""
        self.keywords = json.dumps(keywords_list)

    def get_context_tags(self):
        """Parse context_tags JSON array"""
        if self.context_tags:
            try:
                return json.loads(self.context_tags)
            except json.JSONDecodeError:
                return []
        return []

    def set_context_tags(self, tags_list):
        """Set context tags from list"""
        self.context_tags = json.dumps(tags_list)

    def format_advice(self, **kwargs):
        """
        Format the template with provided variables

        Args:
            **kwargs: Variables to substitute in template (e.g., name="Alex", friend_name="Sam")

        Returns:
            Formatted advice string
        """
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            # Missing variable - return template as-is with placeholders
            return self.template

    def increment_usage(self):
        """Increment usage count"""
        self.usage_count += 1

    def is_appropriate_for_age(self, age):
        """
        Check if template is appropriate for given age

        Args:
            age: User's age

        Returns:
            True if age is within min_age and max_age range
        """
        return self.min_age <= age <= self.max_age

    def is_available_at_friendship_level(self, friendship_level):
        """
        Check if template is available at given friendship level

        Args:
            friendship_level: Current friendship level (1-10)

        Returns:
            True if friendship level meets requirements
        """
        if self.max_friendship_level:
            return self.min_friendship_level <= friendship_level <= self.max_friendship_level
        else:
            return self.min_friendship_level <= friendship_level

    def __repr__(self):
        return f"<AdviceTemplate(id={self.id}, category='{self.category}', level={self.min_friendship_level}-{self.max_friendship_level or '∞'})>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "category": self.category,
            "subcategory": self.subcategory,
            "keywords": self.get_keywords(),
            "template": self.template,
            "min_friendship_level": self.min_friendship_level,
            "max_friendship_level": self.max_friendship_level,
            "min_age": self.min_age,
            "max_age": self.max_age,
            "expert_reviewed": self.expert_reviewed,
            "usage_count": self.usage_count,
            "rating": self.rating,
            "tone": self.tone,
            "response_style": self.response_style,
            "context_tags": self.get_context_tags(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def get_by_category(cls, db, category, friendship_level=1, age=None, subcategory=None):
        """
        Get advice templates for a category available at current friendship level and age

        Args:
            db: Database session
            category: Advice category
            friendship_level: Current friendship level (default: 1)
            age: User's age (optional, filters by age appropriateness)
            subcategory: Optional subcategory filter

        Returns:
            List of AdviceTemplate objects
        """
        query = db.query(cls).filter(
            cls.category == category,
            cls.min_friendship_level <= friendship_level
        )

        # Filter by max friendship level if set
        query = query.filter(
            (cls.max_friendship_level.is_(None)) | (cls.max_friendship_level >= friendship_level)
        )

        # Filter by subcategory if provided
        if subcategory:
            query = query.filter(cls.subcategory == subcategory)

        # Filter by age if provided
        if age:
            query = query.filter(
                cls.min_age <= age,
                cls.max_age >= age
            )

        return query.all()

    @classmethod
    def get_expert_reviewed(cls, db, category=None):
        """
        Get only expert-reviewed templates, optionally filtered by category

        Args:
            db: Database session
            category: Optional category filter

        Returns:
            List of expert-reviewed AdviceTemplate objects
        """
        query = db.query(cls).filter(cls.expert_reviewed == True)

        if category:
            query = query.filter(cls.category == category)

        return query.all()

    @classmethod
    def get_most_used(cls, db, category=None, limit=10):
        """
        Get most frequently used templates

        Args:
            db: Database session
            category: Optional category filter
            limit: Maximum number of templates to return

        Returns:
            List of AdviceTemplate objects ordered by usage_count
        """
        query = db.query(cls)

        if category:
            query = query.filter(cls.category == category)

        return query.order_by(cls.usage_count.desc()).limit(limit).all()

    @classmethod
    def get_by_tone(cls, db, tone, category=None):
        """
        Get templates with specific tone

        Args:
            db: Database session
            tone: Desired tone (supportive, encouraging, empathetic, practical)
            category: Optional category filter

        Returns:
            List of AdviceTemplate objects
        """
        query = db.query(cls).filter(cls.tone == tone)

        if category:
            query = query.filter(cls.category == category)

        return query.all()
