"""
Test short-term memory context (last 3 conversations)

Run with: pytest backend/tests/test_short_term_memory.py -v
"""

import pytest
import sys
import os
from datetime import datetime, timedelta

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, backend_path)

from services.conversation_manager import conversation_manager
from database.database import SessionLocal, init_db
from models.user import User
from models.conversation import Conversation, Message


@pytest.fixture(scope="module")
def db_session():
    """Create a database session for tests"""
    init_db()
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="module")
def test_user(db_session):
    """Create a test user"""
    user = User(id=8888, name="ShortTermTestUser")
    db_session.add(user)
    db_session.commit()
    yield user
    # Cleanup
    db_session.delete(user)
    db_session.commit()


class TestShortTermMemory:
    """Tests for short-term memory context from last 3 conversations"""

    def test_get_short_term_memory_no_conversations(self, db_session, test_user):
        """Test with no conversation history"""
        messages = conversation_manager._get_short_term_memory(test_user.id, db_session)
        assert messages == [], "Should return empty list when no conversations exist"

    def test_get_short_term_memory_one_conversation(self, db_session, test_user):
        """Test with one conversation"""
        # Create one conversation
        conv1 = Conversation(
            user_id=test_user.id,
            timestamp=datetime.now() - timedelta(hours=2),
            message_count=3
        )
        db_session.add(conv1)
        db_session.commit()
        db_session.refresh(conv1)

        # Add messages to conversation
        msg1 = Message(
            conversation_id=conv1.id,
            role="user",
            content="Hello!",
            timestamp=datetime.now() - timedelta(hours=2)
        )
        msg2 = Message(
            conversation_id=conv1.id,
            role="assistant",
            content="Hi there!",
            timestamp=datetime.now() - timedelta(hours=2, minutes=-1)
        )
        msg3 = Message(
            conversation_id=conv1.id,
            role="user",
            content="How are you?",
            timestamp=datetime.now() - timedelta(hours=2, minutes=-2)
        )
        db_session.add_all([msg1, msg2, msg3])
        db_session.commit()

        # Get short-term memory
        messages = conversation_manager._get_short_term_memory(test_user.id, db_session)

        assert len(messages) == 3, "Should retrieve all 3 messages from the conversation"
        assert messages[0].content == "Hello!", "Messages should be in chronological order"
        assert messages[1].content == "Hi there!"
        assert messages[2].content == "How are you?"

        # Cleanup
        db_session.delete(msg1)
        db_session.delete(msg2)
        db_session.delete(msg3)
        db_session.delete(conv1)
        db_session.commit()

    def test_get_short_term_memory_three_conversations(self, db_session, test_user):
        """Test with exactly 3 conversations"""
        # Create 3 conversations at different times
        conv1 = Conversation(
            user_id=test_user.id,
            timestamp=datetime.now() - timedelta(days=3),
            message_count=2
        )
        conv2 = Conversation(
            user_id=test_user.id,
            timestamp=datetime.now() - timedelta(days=2),
            message_count=2
        )
        conv3 = Conversation(
            user_id=test_user.id,
            timestamp=datetime.now() - timedelta(days=1),
            message_count=2
        )
        db_session.add_all([conv1, conv2, conv3])
        db_session.commit()
        db_session.refresh(conv1)
        db_session.refresh(conv2)
        db_session.refresh(conv3)

        # Add messages to each conversation
        messages_to_add = []

        # Conversation 1 messages
        messages_to_add.append(Message(
            conversation_id=conv1.id,
            role="user",
            content="Message from conversation 1",
            timestamp=datetime.now() - timedelta(days=3)
        ))
        messages_to_add.append(Message(
            conversation_id=conv1.id,
            role="assistant",
            content="Response from conversation 1",
            timestamp=datetime.now() - timedelta(days=3, minutes=-1)
        ))

        # Conversation 2 messages
        messages_to_add.append(Message(
            conversation_id=conv2.id,
            role="user",
            content="Message from conversation 2",
            timestamp=datetime.now() - timedelta(days=2)
        ))
        messages_to_add.append(Message(
            conversation_id=conv2.id,
            role="assistant",
            content="Response from conversation 2",
            timestamp=datetime.now() - timedelta(days=2, minutes=-1)
        ))

        # Conversation 3 messages
        messages_to_add.append(Message(
            conversation_id=conv3.id,
            role="user",
            content="Message from conversation 3",
            timestamp=datetime.now() - timedelta(days=1)
        ))
        messages_to_add.append(Message(
            conversation_id=conv3.id,
            role="assistant",
            content="Response from conversation 3",
            timestamp=datetime.now() - timedelta(days=1, minutes=-1)
        ))

        db_session.add_all(messages_to_add)
        db_session.commit()

        # Get short-term memory
        messages = conversation_manager._get_short_term_memory(test_user.id, db_session)

        assert len(messages) == 6, "Should retrieve all messages from all 3 conversations"

        # Verify messages are in chronological order (oldest to newest)
        assert "conversation 1" in messages[0].content, "First message should be from conversation 1"
        assert "conversation 2" in messages[2].content, "Middle messages should be from conversation 2"
        assert "conversation 3" in messages[4].content, "Last messages should be from conversation 3"

        # Cleanup
        for msg in messages_to_add:
            db_session.delete(msg)
        db_session.delete(conv1)
        db_session.delete(conv2)
        db_session.delete(conv3)
        db_session.commit()

    def test_get_short_term_memory_more_than_three_conversations(self, db_session, test_user):
        """Test that only last 3 conversations are included"""
        # Create 5 conversations
        conversations = []
        for i in range(5):
            conv = Conversation(
                user_id=test_user.id,
                timestamp=datetime.now() - timedelta(days=5-i),
                message_count=1
            )
            conversations.append(conv)
            db_session.add(conv)

        db_session.commit()
        for conv in conversations:
            db_session.refresh(conv)

        # Add one message to each conversation
        messages_to_add = []
        for i, conv in enumerate(conversations):
            msg = Message(
                conversation_id=conv.id,
                role="user",
                content=f"Message from conversation {i+1}",
                timestamp=datetime.now() - timedelta(days=5-i)
            )
            messages_to_add.append(msg)
            db_session.add(msg)

        db_session.commit()

        # Get short-term memory
        messages = conversation_manager._get_short_term_memory(test_user.id, db_session)

        # Should only get messages from last 3 conversations (3, 4, 5)
        assert len(messages) == 3, "Should only retrieve messages from last 3 conversations"
        assert "conversation 3" in messages[0].content, "Should start with conversation 3"
        assert "conversation 4" in messages[1].content
        assert "conversation 5" in messages[2].content, "Should end with conversation 5"

        # Should NOT include conversation 1 or 2
        message_contents = [m.content for m in messages]
        assert not any("conversation 1" in c for c in message_contents), "Should not include conversation 1"
        assert not any("conversation 2" in c for c in message_contents), "Should not include conversation 2"

        # Cleanup
        for msg in messages_to_add:
            db_session.delete(msg)
        for conv in conversations:
            db_session.delete(conv)
        db_session.commit()

    def test_get_short_term_memory_limits_messages_per_conversation(self, db_session, test_user):
        """Test that messages are limited per conversation"""
        # Create one conversation with many messages
        conv = Conversation(
            user_id=test_user.id,
            timestamp=datetime.now() - timedelta(hours=1),
            message_count=20
        )
        db_session.add(conv)
        db_session.commit()
        db_session.refresh(conv)

        # Add 20 messages
        messages_to_add = []
        for i in range(20):
            msg = Message(
                conversation_id=conv.id,
                role="user" if i % 2 == 0 else "assistant",
                content=f"Message {i+1}",
                timestamp=datetime.now() - timedelta(hours=1, minutes=i)
            )
            messages_to_add.append(msg)
            db_session.add(msg)

        db_session.commit()

        # Get short-term memory
        messages = conversation_manager._get_short_term_memory(test_user.id, db_session)

        # Should limit to 5 messages per conversation
        assert len(messages) == 5, "Should limit to 5 messages per conversation"

        # Should get the most recent 5 messages
        assert "Message 16" in messages[0].content or "Message 17" in messages[0].content or "Message 18" in messages[0].content or "Message 19" in messages[0].content or "Message 20" in messages[0].content

        # Cleanup
        for msg in messages_to_add:
            db_session.delete(msg)
        db_session.delete(conv)
        db_session.commit()

    def test_build_context_uses_short_term_memory(self, db_session, test_user):
        """Test that _build_context uses short-term memory"""
        from models.personality import BotPersonality

        # Create personality for user
        personality = BotPersonality(
            user_id=test_user.id,
            name="TestBot",
            mood="happy",
            friendship_level=1
        )
        db_session.add(personality)
        db_session.commit()
        db_session.refresh(personality)

        # Create 2 conversations with messages
        conv1 = Conversation(
            user_id=test_user.id,
            timestamp=datetime.now() - timedelta(hours=2),
            message_count=2
        )
        conv2 = Conversation(
            user_id=test_user.id,
            timestamp=datetime.now() - timedelta(hours=1),
            message_count=2
        )
        db_session.add_all([conv1, conv2])
        db_session.commit()
        db_session.refresh(conv1)
        db_session.refresh(conv2)

        messages_to_add = [
            Message(
                conversation_id=conv1.id,
                role="user",
                content="I like pizza",
                timestamp=datetime.now() - timedelta(hours=2)
            ),
            Message(
                conversation_id=conv1.id,
                role="assistant",
                content="Pizza is great!",
                timestamp=datetime.now() - timedelta(hours=2, minutes=-1)
            ),
            Message(
                conversation_id=conv2.id,
                role="user",
                content="My favorite color is blue",
                timestamp=datetime.now() - timedelta(hours=1)
            ),
            Message(
                conversation_id=conv2.id,
                role="assistant",
                content="Blue is a nice color!",
                timestamp=datetime.now() - timedelta(hours=1, minutes=-1)
            ),
        ]
        db_session.add_all(messages_to_add)
        db_session.commit()

        # Build context
        context = conversation_manager._build_context(
            "What's my favorite food?",
            test_user.id,
            personality,
            db_session
        )

        # Check that recent_messages includes messages from both conversations
        recent_messages = context["recent_messages"]
        assert len(recent_messages) == 4, "Should include messages from both conversations"

        message_contents = [m.content for m in recent_messages]
        assert "pizza" in " ".join(message_contents).lower(), "Should include message about pizza"
        assert "blue" in " ".join(message_contents).lower(), "Should include message about blue"

        # Cleanup
        for msg in messages_to_add:
            db_session.delete(msg)
        db_session.delete(conv1)
        db_session.delete(conv2)
        db_session.delete(personality)
        db_session.commit()


# Pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "short_term_memory: marks tests for short-term memory feature"
    )
