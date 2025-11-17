"""
Personality Drift model
Tracks personality trait changes over time based on conversation metrics
"""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import json

from database.database import Base


class PersonalityDrift(Base):
    """
    PersonalityDrift model - tracks personality trait changes over time

    The bot's personality traits drift gradually based on conversation patterns:
    - User behavior influences trait adjustments
    - Drift is gradual and bounded
    - All changes are logged for transparency

    Relationships:
        - Many-to-one with User
    """

    __tablename__ = "personality_drift"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # What changed
    trait_name = Column(String, nullable=False)  # humor, energy, curiosity, formality
    old_value = Column(Float, nullable=False)
    new_value = Column(Float, nullable=False)
    change_amount = Column(Float, nullable=False)  # Can be positive or negative

    # Why it changed
    trigger_type = Column(String, nullable=False)  # conversation_pattern, user_feedback, level_up, manual
    trigger_details = Column(Text, nullable=True)  # JSON with specific reasons

    # Context
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True)
    friendship_level = Column(Integer, nullable=False)

    # When
    timestamp = Column(DateTime, default=datetime.now, nullable=False)

    # Relationships
    user = relationship("User", back_populates="personality_drifts")
    conversation = relationship("Conversation")

    def get_trigger_details(self):
        """Parse trigger details JSON"""
        if self.trigger_details:
            try:
                return json.loads(self.trigger_details)
            except json.JSONDecodeError:
                return {}
        return {}

    def set_trigger_details(self, details_dict):
        """Set trigger details from dictionary"""
        self.trigger_details = json.dumps(details_dict)

    def __repr__(self):
        return (
            f"<PersonalityDrift(id={self.id}, trait='{self.trait_name}', "
            f"change={self.change_amount:+.3f}, trigger='{self.trigger_type}')>"
        )

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "trait_name": self.trait_name,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "change_amount": self.change_amount,
            "trigger_type": self.trigger_type,
            "trigger_details": self.get_trigger_details(),
            "conversation_id": self.conversation_id,
            "friendship_level": self.friendship_level,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
