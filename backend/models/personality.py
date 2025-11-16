"""
BotPersonality model
Represents the chatbot's personality state for a user
"""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import json

from database.database import Base


class BotPersonality(Base):
    """
    BotPersonality model - stores the bot's personality for each user

    The personality evolves over time through:
    - Trait adjustments based on conversation patterns
    - Friendship level progression
    - Mood changes based on context
    - Quirk development

    Relationships:
        - Many-to-one with User (one personality per user)
    """

    __tablename__ = "bot_personality"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    # Bot identity
    name = Column(String, nullable=False, default="Buddy")

    # Personality traits (0.0 to 1.0)
    humor = Column(Float, default=0.5, nullable=False)           # Frequency of jokes
    energy = Column(Float, default=0.6, nullable=False)          # Enthusiasm level
    curiosity = Column(Float, default=0.5, nullable=False)       # How often bot asks questions
    formality = Column(Float, default=0.3, nullable=False)       # Casual vs formal language

    # Friendship progression
    friendship_level = Column(Integer, default=1, nullable=False)     # 1-10
    total_conversations = Column(Integer, default=0, nullable=False)

    # Current state
    mood = Column(String, default="happy", nullable=False)  # happy, excited, calm, concerned, playful, thoughtful

    # Personality features (JSON arrays stored as text)
    quirks = Column(Text, nullable=True)          # JSON: ['uses_emojis', 'tells_puns', ...]
    interests = Column(Text, nullable=True)       # JSON: ['sports', 'music', 'science', ...]
    catchphrase = Column(String, nullable=True)   # Developed at friendship level 3+

    # Timestamps
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    # Relationships
    user = relationship("User", back_populates="personality")

    def get_quirks(self):
        """Parse quirks JSON array"""
        if self.quirks:
            try:
                return json.loads(self.quirks)
            except json.JSONDecodeError:
                return []
        return []

    def set_quirks(self, quirks_list):
        """Set quirks from list"""
        self.quirks = json.dumps(quirks_list)

    def get_interests(self):
        """Parse interests JSON array"""
        if self.interests:
            try:
                return json.loads(self.interests)
            except json.JSONDecodeError:
                return []
        return []

    def set_interests(self, interests_list):
        """Set interests from list"""
        self.interests = json.dumps(interests_list)

    def __repr__(self):
        return f"<BotPersonality(id={self.id}, name='{self.name}', level={self.friendship_level}, mood='{self.mood}')>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "traits": {
                "humor": self.humor,
                "energy": self.energy,
                "curiosity": self.curiosity,
                "formality": self.formality,
            },
            "friendship_level": self.friendship_level,
            "total_conversations": self.total_conversations,
            "mood": self.mood,
            "quirks": self.get_quirks(),
            "interests": self.get_interests(),
            "catchphrase": self.catchphrase,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
