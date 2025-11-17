"""
Test context builder functionality

Run with: pytest backend/tests/test_context_builder.py -v
"""

import pytest
import sys
import os
from datetime import datetime, timedelta

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, backend_path)

from services.memory_manager import memory_manager
from database.database import SessionLocal, init_db
from models.user import User
from models.memory import UserProfile
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
    user = User(id=9994, name="ContextTestUser")
    db_session.add(user)
    db_session.commit()
    yield user
    # Cleanup
    db_session.query(Message).filter(Message.user_id == user.id).delete()
    db_session.query(Conversation).filter(Conversation.user_id == user.id).delete()
    db_session.query(UserProfile).filter(UserProfile.user_id == user.id).delete()
    db_session.delete(user)
    db_session.commit()


@pytest.fixture(scope="module")
def test_conversation(db_session, test_user):
    """Create a test conversation with messages"""
    conversation = Conversation(
        user_id=test_user.id,
        title="Test Conversation",
        timestamp=datetime.now()
    )
    db_session.add(conversation)
    db_session.commit()

    # Add some messages
    messages = [
        Message(
            conversation_id=conversation.id,
            user_id=test_user.id,
            role="user",
            content="I love playing soccer",
            timestamp=datetime.now() - timedelta(minutes=5)
        ),
        Message(
            conversation_id=conversation.id,
            user_id=test_user.id,
            role="assistant",
            content="That's great! Soccer is a fun sport.",
            timestamp=datetime.now() - timedelta(minutes=4)
        ),
        Message(
            conversation_id=conversation.id,
            user_id=test_user.id,
            role="user",
            content="I want to make the soccer team",
            timestamp=datetime.now() - timedelta(minutes=3)
        ),
    ]
    db_session.add_all(messages)
    db_session.commit()

    yield conversation

    # Cleanup handled by test_user fixture


@pytest.fixture(scope="module")
def test_memories(db_session, test_user):
    """Create test memories"""
    memories = []

    # Favorites
    memories.append(memory_manager.add_favorite(test_user.id, "sport", "soccer", db_session))
    memories.append(memory_manager.add_favorite(test_user.id, "color", "blue", db_session))

    # Goals
    memories.append(memory_manager.add_goal(test_user.id, "sports", "make the soccer team", db_session))
    memories.append(memory_manager.add_goal(test_user.id, "academic", "get all A's", db_session))

    # People
    memories.append(memory_manager.add_person(test_user.id, "friend_emma", "best friend who plays soccer", db_session))

    # Achievements
    memories.append(memory_manager.add_achievement(test_user.id, "sports", "won championship", db_session))

    yield memories

    # Cleanup handled by test_user fixture


class TestContextBuilder:
    """Tests for context builder"""

    def test_build_context_basic(self, db_session, test_user, test_memories):
        """Test basic context building"""
        context = memory_manager.build_context(
            user_id=test_user.id,
            db=db_session
        )

        assert "user_id" in context
        assert context["user_id"] == test_user.id
        assert "recent_messages" in context
        assert "top_memories" in context
        assert "searched_memories" in context
        assert "total_memories_count" in context

    def test_build_context_with_top_memories(self, db_session, test_user, test_memories):
        """Test that top memories are included"""
        context = memory_manager.build_context(
            user_id=test_user.id,
            db=db_session,
            include_top_memories=True,
            max_memories=5
        )

        assert len(context["top_memories"]) > 0, "Should include top memories"
        assert len(context["top_memories"]) <= 5, "Should respect max_memories limit"

        # Each top memory should have relevance score
        for item in context["top_memories"]:
            assert "memory" in item
            assert "relevance_score" in item
            assert 0 <= item["relevance_score"] <= 100

    def test_build_context_with_conversation(self, db_session, test_user, test_conversation):
        """Test that recent messages are included"""
        context = memory_manager.build_context(
            user_id=test_user.id,
            db=db_session,
            conversation_id=test_conversation.id,
            include_recent_messages=True
        )

        assert len(context["recent_messages"]) > 0, "Should include recent messages"

        # Check message structure
        for msg in context["recent_messages"]:
            assert "role" in msg
            assert "content" in msg
            assert "timestamp" in msg

    def test_build_context_with_keyword_search(self, db_session, test_user, test_memories):
        """Test that keyword search finds relevant memories"""
        context = memory_manager.build_context(
            user_id=test_user.id,
            db=db_session,
            current_message="I love playing soccer with my friends",
            include_searched_memories=True
        )

        assert len(context["searched_memories"]) > 0, "Should find memories related to soccer"

        # Check that soccer-related memories are found
        found_soccer = any(
            "soccer" in item["memory"]["value"].lower()
            for item in context["searched_memories"]
        )
        assert found_soccer, "Should find soccer-related memories"

    def test_extract_keywords_from_message(self, db_session, test_user):
        """Test keyword extraction from messages"""
        message = "I love playing soccer and basketball with my friends"
        keywords = memory_manager._extract_keywords_from_message(message)

        assert isinstance(keywords, list), "Should return a list"
        assert "love" in keywords, "Should extract 'love'"
        assert "playing" in keywords, "Should extract 'playing'"
        assert "soccer" in keywords, "Should extract 'soccer'"
        assert "basketball" in keywords, "Should extract 'basketball'"
        assert "friends" in keywords, "Should extract 'friends'"

        # Stopwords should be filtered out
        assert "I" not in keywords, "Should filter out stopword 'I'"
        assert "and" not in keywords, "Should filter out stopword 'and'"
        assert "with" not in keywords, "Should filter out stopword 'with'"
        assert "my" not in keywords, "Should filter out stopword 'my'"

    def test_extract_keywords_filters_short_words(self, db_session, test_user):
        """Test that short words are filtered"""
        message = "I go to my school"
        keywords = memory_manager._extract_keywords_from_message(message)

        # "go" and "to" are 2 characters or less, should be filtered
        assert "go" not in keywords, "Should filter words <= 2 characters"
        assert "school" in keywords, "Should keep longer words"

    def test_extract_keywords_deduplicates(self, db_session, test_user):
        """Test that keywords are deduplicated"""
        message = "soccer soccer soccer basketball"
        keywords = memory_manager._extract_keywords_from_message(message)

        assert keywords.count("soccer") == 1, "Should deduplicate keywords"
        assert len(keywords) == 2, "Should have 2 unique keywords"

    def test_extract_keywords_empty_message(self, db_session, test_user):
        """Test keyword extraction from empty message"""
        keywords = memory_manager._extract_keywords_from_message("")

        assert keywords == [], "Empty message should return empty list"

    def test_format_context_for_llm_basic(self, db_session, test_user, test_memories):
        """Test basic LLM context formatting"""
        context = memory_manager.build_context(
            user_id=test_user.id,
            db=db_session,
            include_top_memories=True
        )

        formatted = memory_manager.format_context_for_llm(context)

        assert isinstance(formatted, str), "Should return a string"
        assert len(formatted) > 0, "Should not be empty"

    def test_format_context_includes_profile(self, db_session, test_user, test_memories):
        """Test that formatted context includes user profile"""
        context = memory_manager.build_context(
            user_id=test_user.id,
            db=db_session,
            include_top_memories=True
        )

        formatted = memory_manager.format_context_for_llm(
            context,
            include_user_profile=True
        )

        assert "What I Know About You" in formatted, "Should include profile section"

    def test_format_context_groups_by_category(self, db_session, test_user, test_memories):
        """Test that memories are grouped by category"""
        context = memory_manager.build_context(
            user_id=test_user.id,
            db=db_session,
            include_top_memories=True
        )

        formatted = memory_manager.format_context_for_llm(context)

        # Should have category headers
        assert "Favorites:" in formatted or "Goals:" in formatted

    def test_format_context_includes_conversation(self, db_session, test_user, test_conversation):
        """Test that formatted context includes conversation history"""
        context = memory_manager.build_context(
            user_id=test_user.id,
            db=db_session,
            conversation_id=test_conversation.id,
            include_recent_messages=True
        )

        formatted = memory_manager.format_context_for_llm(
            context,
            include_recent_conversation=True
        )

        assert "Recent Conversation" in formatted, "Should include conversation section"
        assert "User:" in formatted or "Assistant:" in formatted

    def test_format_context_deduplicates_memories(self, db_session, test_user, test_memories):
        """Test that searched memories are deduplicated with top memories"""
        context = memory_manager.build_context(
            user_id=test_user.id,
            db=db_session,
            current_message="soccer",
            include_top_memories=True,
            include_searched_memories=True
        )

        formatted = memory_manager.format_context_for_llm(context)

        # Count how many times "soccer" appears (should not be heavily duplicated)
        # This is a basic check - the deduplication logic prevents same memory appearing twice
        assert formatted.count("soccer") < 10, "Should not heavily duplicate memories"

    def test_build_context_without_options(self, db_session, test_user):
        """Test building context with all options disabled"""
        context = memory_manager.build_context(
            user_id=test_user.id,
            db=db_session,
            include_recent_messages=False,
            include_top_memories=False,
            include_searched_memories=False
        )

        assert len(context["recent_messages"]) == 0
        assert len(context["top_memories"]) == 0
        assert len(context["searched_memories"]) == 0

    def test_build_context_max_memories_limit(self, db_session, test_user, test_memories):
        """Test that max_memories limit is respected"""
        context = memory_manager.build_context(
            user_id=test_user.id,
            db=db_session,
            max_memories=2,
            include_top_memories=True
        )

        assert len(context["top_memories"]) <= 2, "Should respect max_memories limit"

    def test_build_context_total_count(self, db_session, test_user, test_memories):
        """Test that total memory count is accurate"""
        context = memory_manager.build_context(
            user_id=test_user.id,
            db=db_session
        )

        assert context["total_memories_count"] > 0, "Should count total memories"
        assert context["total_memories_count"] >= len(test_memories), "Count should be accurate"

    def test_user_isolation_in_context(self, db_session):
        """Test that context is isolated by user"""
        # Create two users
        user1 = User(id=10015, name="User1")
        user2 = User(id=10016, name="User2")
        db_session.add_all([user1, user2])
        db_session.commit()

        # Add memories for each user
        m1 = memory_manager.add_favorite(user1.id, "sport", "basketball", db_session)
        m2 = memory_manager.add_favorite(user2.id, "sport", "tennis", db_session)

        # Build context for each user
        context1 = memory_manager.build_context(user1.id, db_session, include_top_memories=True)
        context2 = memory_manager.build_context(user2.id, db_session, include_top_memories=True)

        # Each user should only see their own memories
        user1_values = [
            item["memory"]["value"]
            for item in context1["top_memories"]
        ]
        user2_values = [
            item["memory"]["value"]
            for item in context2["top_memories"]
        ]

        assert "basketball" in user1_values, "User1 should see basketball"
        assert "basketball" not in user2_values, "User2 should not see basketball"
        assert "tennis" in user2_values, "User2 should see tennis"
        assert "tennis" not in user1_values, "User1 should not see tennis"

        # Cleanup
        db_session.delete(m1)
        db_session.delete(m2)
        db_session.delete(user1)
        db_session.delete(user2)
        db_session.commit()

    def test_keyword_extraction_preserves_order(self, db_session, test_user):
        """Test that keyword extraction preserves first occurrence order"""
        message = "soccer basketball tennis soccer"  # soccer appears twice
        keywords = memory_manager._extract_keywords_from_message(message)

        # Should preserve order of first occurrence
        assert keywords.index("soccer") < keywords.index("basketball")
        assert keywords.index("basketball") < keywords.index("tennis")

    def test_keyword_extraction_limits_to_10(self, db_session, test_user):
        """Test that keyword extraction limits to 10 keywords"""
        # Create message with many keywords
        words = ["word" + str(i) for i in range(20)]
        message = " ".join(words)
        keywords = memory_manager._extract_keywords_from_message(message)

        assert len(keywords) <= 10, "Should limit to 10 keywords"


# Pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "context: marks tests for context builder feature"
    )
