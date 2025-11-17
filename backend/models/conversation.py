"""
Conversation and Message models
Represents conversation sessions and individual messages
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import json

from database.database import Base


class Conversation(Base):
    """
    Conversation model - represents a conversation session

    A conversation is a continuous chat session from start to end.
    Contains multiple messages and metadata about the session.

    Relationships:
        - Many-to-one with User
        - One-to-many with Message
    """

    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Conversation metadata
    timestamp = Column(DateTime, default=datetime.now, nullable=False)
    conversation_summary = Column(Text, nullable=True)  # Generated summary after conversation ends
    mood_detected = Column(String, nullable=True)       # Overall user mood during conversation
    topics = Column(Text, nullable=True)                # JSON array of topics discussed

    # Metrics
    duration_seconds = Column(Integer, nullable=True)
    message_count = Column(Integer, nullable=True)

    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.timestamp")

    def get_topics(self):
        """Parse topics JSON array"""
        if self.topics:
            try:
                return json.loads(self.topics)
            except json.JSONDecodeError:
                return []
        return []

    def set_topics(self, topics_list):
        """Set topics from list"""
        self.topics = json.dumps(topics_list)

    def __repr__(self):
        return f"<Conversation(id={self.id}, user_id={self.user_id}, messages={self.message_count}, duration={self.duration_seconds}s)>"

    def to_dict(self, include_messages=False):
        """Convert to dictionary for API responses"""
        result = {
            "id": self.id,
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "conversation_summary": self.conversation_summary,
            "mood_detected": self.mood_detected,
            "topics": self.get_topics(),
            "duration_seconds": self.duration_seconds,
            "message_count": self.message_count,
        }

        if include_messages and self.messages:
            result["messages"] = [msg.to_dict() for msg in self.messages]

        return result


class Message(Base):
    """
    Message model - represents a single message in a conversation

    Can be either from the user or the assistant (bot).
    Includes safety flagging and optional metadata.

    Relationships:
        - Many-to-one with Conversation
        - One-to-many with SafetyFlag
    """

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)

    # Message content
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.now, nullable=False)

    # Safety
    flagged = Column(Boolean, default=False, nullable=False)

    # Optional metadata (JSON) - renamed to avoid SQLAlchemy conflict
    message_metadata = Column(Text, nullable=True)  # Can store mood detected, topics, etc.

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    safety_flags = relationship("SafetyFlag", back_populates="message", cascade="all, delete-orphan")

    def get_metadata(self):
        """Parse metadata JSON"""
        if self.message_metadata:
            try:
                return json.loads(self.message_metadata)
            except json.JSONDecodeError:
                return {}
        return {}

    def set_metadata(self, metadata_dict):
        """Set metadata from dictionary"""
        self.message_metadata = json.dumps(metadata_dict)

    def __repr__(self):
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<Message(id={self.id}, role='{self.role}', content='{content_preview}')>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "flagged": self.flagged,
            "metadata": self.get_metadata(),
        }
