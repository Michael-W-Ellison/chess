"""
LevelUpEvent model
Tracks friendship level-up events and rewards
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import json

from database.database import Base


class LevelUpEvent(Base):
    """
    LevelUpEvent model - stores friendship level-up events

    Tracks when users reach new friendship levels, including:
    - Level reached and timestamp
    - Rewards unlocked
    - Celebration message
    - Whether user has acknowledged the event

    Relationships:
        - Many-to-one with User
    """

    __tablename__ = "level_up_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Level information
    old_level = Column(Integer, nullable=False)
    new_level = Column(Integer, nullable=False)
    level_name = Column(String, nullable=False)  # e.g., "Best Friend", "Soul Friend"

    # Points information
    friendship_points = Column(Integer, nullable=False)  # Total points when leveled up
    points_earned = Column(Integer, nullable=False)      # Points that triggered level-up

    # Event metadata
    timestamp = Column(DateTime, default=datetime.now, nullable=False)
    celebration_message = Column(Text, nullable=False)

    # Rewards (JSON array stored as text)
    rewards = Column(Text, nullable=True)  # JSON: ['catchphrase_unlocked', 'new_feature', ...]

    # User interaction
    acknowledged = Column(Boolean, default=False, nullable=False)  # Has user seen this event?
    acknowledged_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="level_up_events")

    def get_rewards(self):
        """Parse rewards JSON array"""
        if self.rewards:
            try:
                return json.loads(self.rewards)
            except json.JSONDecodeError:
                return []
        return []

    def set_rewards(self, rewards_list):
        """Set rewards from list"""
        self.rewards = json.dumps(rewards_list)

    def acknowledge(self):
        """Mark event as acknowledged by user"""
        self.acknowledged = True
        self.acknowledged_at = datetime.now()

    def __repr__(self):
        return f"<LevelUpEvent(id={self.id}, user_id={self.user_id}, {self.old_level}->{self.new_level}, '{self.level_name}')>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "old_level": self.old_level,
            "new_level": self.new_level,
            "level_name": self.level_name,
            "friendship_points": self.friendship_points,
            "points_earned": self.points_earned,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "celebration_message": self.celebration_message,
            "rewards": self.get_rewards(),
            "acknowledged": self.acknowledged,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
        }
