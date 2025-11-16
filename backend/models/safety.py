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

    Categories:
        - school_stress
        - friend_conflict
        - performance_anxiety
        - family_issues
        - boredom
        - self_confidence
    """

    __tablename__ = "advice_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Template details
    category = Column(String, nullable=False)                    # Advice category
    keywords = Column(Text, nullable=False)                      # JSON array of trigger keywords
    template = Column(Text, nullable=False)                      # Advice text with {placeholders}
    min_friendship_level = Column(Integer, default=1, nullable=False)
    expert_reviewed = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=datetime.now, nullable=False)

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

    def format_advice(self, **kwargs):
        """
        Format the template with provided variables

        Args:
            **kwargs: Variables to substitute in template (e.g., name="Alex")

        Returns:
            Formatted advice string
        """
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            # Missing variable - return template as-is
            return self.template

    def __repr__(self):
        return f"<AdviceTemplate(id={self.id}, category='{self.category}', level={self.min_friendship_level})>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "category": self.category,
            "keywords": self.get_keywords(),
            "template": self.template,
            "min_friendship_level": self.min_friendship_level,
            "expert_reviewed": self.expert_reviewed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def get_by_category(cls, db, category, friendship_level=1):
        """
        Get advice templates for a category available at current friendship level

        Args:
            db: Database session
            category: Advice category
            friendship_level: Current friendship level

        Returns:
            List of AdviceTemplate objects
        """
        return db.query(cls).filter(
            cls.category == category,
            cls.min_friendship_level <= friendship_level
        ).all()
