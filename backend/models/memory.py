"""
UserProfile (Memory) model
Stores extracted facts and memories about the user
"""

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from database.database import Base


class UserProfile(Base):
    """
    UserProfile model - stores extracted memories and facts about the user

    Each row represents a single fact or memory item.
    Categories include: favorite, dislike, goal, person, achievement

    Examples:
        - category='favorite', key='color', value='blue'
        - category='person', key='friend_emma', value='best friend who likes soccer'
        - category='goal', key='make_soccer_team', value='tryout next week'

    The bot uses these to personalize conversations and demonstrate memory.

    Relationships:
        - Many-to-one with User
    """

    __tablename__ = "user_profile"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Memory categorization
    category = Column(String, nullable=False)  # 'favorite', 'dislike', 'goal', 'person', 'achievement'
    key = Column(String, nullable=False)       # e.g., 'favorite_color', 'friend_name', 'goal_soccer'
    value = Column(Text, nullable=False)       # The actual information

    # Confidence and frequency
    confidence = Column(Float, default=1.0, nullable=False)  # How certain we are (0.0-1.0)
    first_mentioned = Column(DateTime, default=datetime.now, nullable=False)
    last_mentioned = Column(DateTime, default=datetime.now, nullable=False)
    mention_count = Column(Integer, default=1, nullable=False)

    # Relationships
    user = relationship("User", back_populates="profile_items")

    def __repr__(self):
        value_preview = self.value[:30] + "..." if len(self.value) > 30 else self.value
        return f"<UserProfile(id={self.id}, category='{self.category}', key='{self.key}', value='{value_preview}')>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "category": self.category,
            "key": self.key,
            "value": self.value,
            "confidence": self.confidence,
            "first_mentioned": self.first_mentioned.isoformat() if self.first_mentioned else None,
            "last_mentioned": self.last_mentioned.isoformat() if self.last_mentioned else None,
            "mention_count": self.mention_count,
        }

    @classmethod
    def get_by_category(cls, db, user_id, category):
        """
        Get all profile items for a user in a specific category

        Args:
            db: Database session
            user_id: User ID
            category: Category to filter by

        Returns:
            List of UserProfile objects
        """
        return db.query(cls).filter(
            cls.user_id == user_id,
            cls.category == category
        ).all()

    @classmethod
    def get_favorites(cls, db, user_id):
        """Get all favorites as a dictionary"""
        favorites = cls.get_by_category(db, user_id, "favorite")
        return {item.key: item.value for item in favorites}

    @classmethod
    def get_dislikes(cls, db, user_id):
        """Get all dislikes as a dictionary"""
        dislikes = cls.get_by_category(db, user_id, "dislike")
        return {item.key: item.value for item in dislikes}

    @classmethod
    def get_people(cls, db, user_id):
        """Get all important people"""
        return cls.get_by_category(db, user_id, "person")

    @classmethod
    def get_goals(cls, db, user_id):
        """Get all goals"""
        return cls.get_by_category(db, user_id, "goal")

    @classmethod
    def get_achievements(cls, db, user_id):
        """Get all achievements"""
        return cls.get_by_category(db, user_id, "achievement")
