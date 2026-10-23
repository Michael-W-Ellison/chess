"""
Tests for the greeting at the start of a conversation (ConversationManager._generate_greeting)
"""

from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.database import Base
from models.conversation import Conversation, Message
from models.level_up_event import LevelUpEvent  # noqa: F401  (resolves the BotPersonality relationship)
from models.personality import BotPersonality
from models.user import User
from services.conversation_manager import ConversationManager


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


def setup(db, name="User", previous_at=None, last_message_at=None):
    user = User(id=1, name=name)
    personality = BotPersonality(user_id=1, name="Buddy")
    db.add_all([user, personality])
    if previous_at is not None:
        previous = Conversation(user_id=1, timestamp=previous_at)
        db.add(previous)
        db.flush()
        if last_message_at is not None:
            db.add(Message(conversation_id=previous.id, role="user", content="hi", timestamp=last_message_at))
    current = Conversation(user_id=1, timestamp=datetime.now())
    db.add(current)
    db.commit()
    return user, personality, current


def greet(db, **kwargs):
    user, personality, current = setup(db, **kwargs)
    return ConversationManager()._generate_greeting(user, personality, db, current.id)


def test_first_conversation_introduces_the_bot(db):
    assert greet(db) == "Hi there! I'm Buddy, your new friend. What's your name?"


def test_first_conversation_with_a_known_name(db):
    assert greet(db, name="Ezri").startswith("Hi Ezri! I'm Buddy")


def test_placeholder_name_is_not_used(db):
    greeting = greet(db, previous_at=datetime.now() - timedelta(minutes=10))
    assert "User" not in greeting
    assert greeting == "Hey there! Back already? What's up?"


def test_conversation_just_started_does_not_count(db):
    greeting = greet(db, name="Ezri", previous_at=datetime.now() - timedelta(days=3))
    assert "missed you" in greeting


@pytest.mark.parametrize("hours,expected", [
    (0.5, "Back already?"), (5, "How are you doing?"), (30, "Good to see you again!"), (72, "I missed you!"),
])
def test_time_since_last_chat_counts_whole_days(db, hours, expected):
    assert expected in greet(db, name="Ezri", previous_at=datetime.now() - timedelta(hours=hours))


def test_time_is_measured_from_the_last_message(db):
    # A long conversation started 5 hours ago that ended 10 minutes ago
    greeting = greet(db, name="Ezri", previous_at=datetime.now() - timedelta(hours=5),
                     last_message_at=datetime.now() - timedelta(minutes=10))
    assert "Back already?" in greeting
