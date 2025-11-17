"""
User model
Represents a user of the chatbot
"""

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from database.database import Base


class User(Base):
    """
    User model - represents a chatbot user (preteen child)

    Relationships:
        - One-to-one with BotPersonality
        - One-to-many with Conversation
        - One-to-many with UserProfile (memory items)
        - One-to-many with SafetyFlag
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=True)
    grade = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    last_active = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    parent_email = Column(String, nullable=True)

    # Relationships
    personality = relationship("BotPersonality", back_populates="user", uselist=False, cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    profile_items = relationship("UserProfile", back_populates="user", cascade="all, delete-orphan")
    safety_flags = relationship("SafetyFlag", back_populates="user", cascade="all, delete-orphan")
    level_up_events = relationship("LevelUpEvent", back_populates="user", cascade="all, delete-orphan", order_by="LevelUpEvent.timestamp.desc()")

    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', age={self.age})>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "name": self.name,
            "age": self.age,
            "grade": self.grade,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_active": self.last_active.isoformat() if self.last_active else None,
            "parent_email": self.parent_email,
        }
