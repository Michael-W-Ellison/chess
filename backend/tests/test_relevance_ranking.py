"""
Test memory relevance ranking

Run with: pytest backend/tests/test_relevance_ranking.py -v
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
    user = User(id=9995, name="RankingTestUser")
    db_session.add(user)
    db_session.commit()
    yield user
    # Cleanup
    db_session.query(UserProfile).filter(UserProfile.user_id == user.id).delete()
    db_session.delete(user)
    db_session.commit()


@pytest.fixture(scope="module")
def diverse_memories(db_session, test_user):
    """Create memories with diverse relevance characteristics"""
    memories = []

    # Recent memory with low frequency and confidence
    m1 = UserProfile(
        user_id=test_user.id,
        category="favorite",
        key="recent_low",
        value="new favorite",
        confidence=0.5,
        first_mentioned=datetime.now(),
        last_mentioned=datetime.now(),
        mention_count=1
    )
    memories.append(m1)

    # Old memory with high frequency and confidence
    m2 = UserProfile(
        user_id=test_user.id,
        category="favorite",
        key="old_high",
        value="long-time favorite",
        confidence=1.0,
        first_mentioned=datetime.now() - timedelta(days=365),
        last_mentioned=datetime.now() - timedelta(days=30),
        mention_count=100
    )
    memories.append(m2)

    # Medium recency, medium frequency, high confidence
    m3 = UserProfile(
        user_id=test_user.id,
        category="goal",
        key="balanced",
        value="balanced goal",
        confidence=0.9,
        first_mentioned=datetime.now() - timedelta(days=7),
        last_mentioned=datetime.now() - timedelta(days=3),
        mention_count=10
    )
    memories.append(m3)

    # Very recent, medium frequency, medium confidence
    m4 = UserProfile(
        user_id=test_user.id,
        category="achievement",
        key="very_recent",
        value="just achieved",
        confidence=0.7,
        first_mentioned=datetime.now() - timedelta(hours=2),
        last_mentioned=datetime.now() - timedelta(hours=1),
        mention_count=5
    )
    memories.append(m4)

    # Old, low frequency, low confidence
    m5 = UserProfile(
        user_id=test_user.id,
        category="dislike",
        key="old_low",
        value="old dislike",
        confidence=0.3,
        first_mentioned=datetime.now() - timedelta(days=90),
        last_mentioned=datetime.now() - timedelta(days=60),
        mention_count=2
    )
    memories.append(m5)

    db_session.add_all(memories)
    db_session.commit()

    yield memories

    # Cleanup
    for memory in memories:
        db_session.delete(memory)
    db_session.commit()


class TestRelevanceRanking:
    """Tests for memory relevance ranking"""

    def test_calculate_recency_score(self, db_session, diverse_memories):
        """Test recency-based scoring"""
        very_recent = diverse_memories[3]  # 1 hour ago
        old = diverse_memories[1]  # 30 days ago

        recent_score = memory_manager.calculate_memory_relevance(very_recent, "recency")
        old_score = memory_manager.calculate_memory_relevance(old, "recency")

        assert recent_score > old_score, "More recent memories should score higher"
        assert 0 <= recent_score <= 100, "Scores should be in 0-100 range"
        assert 0 <= old_score <= 100, "Scores should be in 0-100 range"

    def test_calculate_frequency_score(self, db_session, diverse_memories):
        """Test frequency-based scoring"""
        high_freq = diverse_memories[1]  # mention_count = 100
        low_freq = diverse_memories[0]  # mention_count = 1

        high_score = memory_manager.calculate_memory_relevance(high_freq, "frequency")
        low_score = memory_manager.calculate_memory_relevance(low_freq, "frequency")

        assert high_score > low_score, "More frequent memories should score higher"
        assert 0 <= high_score <= 100, "Scores should be in 0-100 range"
        assert 0 <= low_score <= 100, "Scores should be in 0-100 range"

    def test_calculate_confidence_score(self, db_session, diverse_memories):
        """Test confidence-based scoring"""
        high_conf = diverse_memories[1]  # confidence = 1.0
        low_conf = diverse_memories[4]  # confidence = 0.3

        high_score = memory_manager.calculate_memory_relevance(high_conf, "confidence")
        low_score = memory_manager.calculate_memory_relevance(low_conf, "confidence")

        assert high_score > low_score, "Higher confidence should score higher"
        assert high_score == 100, "Confidence 1.0 should give score of 100"
        assert low_score == 30, "Confidence 0.3 should give score of 30"

    def test_calculate_combined_score(self, db_session, diverse_memories):
        """Test combined scoring strategy"""
        balanced = diverse_memories[2]

        combined_score = memory_manager.calculate_memory_relevance(balanced, "combined")

        assert 0 <= combined_score <= 100, "Combined score should be in 0-100 range"
        assert combined_score > 0, "Memory with reasonable stats should have positive score"

    def test_invalid_strategy_raises_error(self, db_session, diverse_memories):
        """Test that invalid strategy raises ValueError"""
        memory = diverse_memories[0]

        with pytest.raises(ValueError, match="Unknown ranking strategy"):
            memory_manager.calculate_memory_relevance(memory, "invalid_strategy")

    def test_get_top_memories_by_recency(self, db_session, test_user, diverse_memories):
        """Test getting top memories by recency"""
        top = memory_manager.get_top_memories(
            user_id=test_user.id,
            db=db_session,
            limit=3,
            strategy="recency"
        )

        assert len(top) <= 3, "Should respect limit"
        assert len(top) > 0, "Should return some results"

        # Most recent should be first
        assert top[0].key == "very_recent", "Most recent memory should rank first"

    def test_get_top_memories_by_frequency(self, db_session, test_user, diverse_memories):
        """Test getting top memories by frequency"""
        top = memory_manager.get_top_memories(
            user_id=test_user.id,
            db=db_session,
            limit=3,
            strategy="frequency"
        )

        assert len(top) <= 3, "Should respect limit"
        assert len(top) > 0, "Should return some results"

        # Highest frequency should be first
        assert top[0].key == "old_high", "Highest frequency memory should rank first"

    def test_get_top_memories_by_confidence(self, db_session, test_user, diverse_memories):
        """Test getting top memories by confidence"""
        top = memory_manager.get_top_memories(
            user_id=test_user.id,
            db=db_session,
            limit=3,
            strategy="confidence"
        )

        assert len(top) <= 3, "Should respect limit"
        assert len(top) > 0, "Should return some results"

        # Highest confidence should be first
        assert top[0].confidence >= top[1].confidence, "Should be ordered by confidence"

    def test_get_top_memories_with_category_filter(self, db_session, test_user, diverse_memories):
        """Test getting top memories with category filter"""
        favorites_only = memory_manager.get_top_memories(
            user_id=test_user.id,
            db=db_session,
            limit=10,
            category="favorite",
            strategy="combined"
        )

        assert all(m.category == "favorite" for m in favorites_only), "All should be favorites"

    def test_get_top_memories_limit(self, db_session, test_user, diverse_memories):
        """Test that limit parameter works correctly"""
        top_1 = memory_manager.get_top_memories(
            user_id=test_user.id,
            db=db_session,
            limit=1,
            strategy="combined"
        )

        top_3 = memory_manager.get_top_memories(
            user_id=test_user.id,
            db=db_session,
            limit=3,
            strategy="combined"
        )

        assert len(top_1) == 1, "Should return only 1 result"
        assert len(top_3) == 3, "Should return 3 results"

    def test_get_memory_importance_breakdown(self, db_session, test_user, diverse_memories):
        """Test getting memory importance breakdown"""
        breakdown = memory_manager.get_memory_importance_breakdown(
            user_id=test_user.id,
            db=db_session
        )

        assert "total_memories" in breakdown, "Should include total count"
        assert breakdown["total_memories"] == 5, "Should count all 5 test memories"

        assert "average_scores" in breakdown, "Should include average scores"
        assert "recency" in breakdown["average_scores"]
        assert "frequency" in breakdown["average_scores"]
        assert "confidence" in breakdown["average_scores"]

        assert "top_by_recency" in breakdown, "Should include top by recency"
        assert "top_by_frequency" in breakdown, "Should include top by frequency"
        assert "top_by_confidence" in breakdown, "Should include top by confidence"
        assert "top_combined" in breakdown, "Should include top by combined score"

        # Each top list should have scores
        for item in breakdown["top_by_recency"]:
            assert "memory" in item
            assert "score" in item
            assert 0 <= item["score"] <= 100

    def test_breakdown_with_category_filter(self, db_session, test_user, diverse_memories):
        """Test importance breakdown with category filter"""
        breakdown = memory_manager.get_memory_importance_breakdown(
            user_id=test_user.id,
            db=db_session,
            category="favorite"
        )

        # Should only count favorites (2 in our test data)
        assert breakdown["total_memories"] == 2, "Should only count favorites"

        # All returned memories should be favorites
        for item in breakdown["top_by_recency"]:
            assert item["memory"]["category"] == "favorite"

    def test_breakdown_empty_category(self, db_session, test_user):
        """Test breakdown when category has no memories"""
        breakdown = memory_manager.get_memory_importance_breakdown(
            user_id=test_user.id,
            db=db_session,
            category="nonexistent"
        )

        assert breakdown["total_memories"] == 0, "Should return 0 for empty category"
        assert breakdown["top_by_recency"] == [], "Should return empty list"

    def test_user_isolation(self, db_session):
        """Test that ranking respects user isolation"""
        # Create two users
        user1 = User(id=10013, name="User1")
        user2 = User(id=10014, name="User2")
        db_session.add_all([user1, user2])
        db_session.commit()

        # Add memories for each user
        m1 = memory_manager.add_favorite(user1.id, "sport", "basketball", db_session)
        m2 = memory_manager.add_favorite(user2.id, "sport", "tennis", db_session)

        # Get top memories for each user
        user1_top = memory_manager.get_top_memories(user1.id, db_session)
        user2_top = memory_manager.get_top_memories(user2.id, db_session)

        # Each user should only see their own memories
        user1_values = [m.value for m in user1_top]
        user2_values = [m.value for m in user2_top]

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

    def test_combined_strategy_weights(self, db_session, test_user):
        """Test that combined strategy applies proper weighting"""
        # Create a memory with known values
        memory = UserProfile(
            user_id=test_user.id,
            category="favorite",
            key="test",
            value="test value",
            confidence=1.0,  # Will give 100 confidence score
            first_mentioned=datetime.now(),
            last_mentioned=datetime.now(),  # Will give ~100 recency score
            mention_count=1  # Will give low frequency score
        )
        db_session.add(memory)
        db_session.commit()

        recency = memory_manager.calculate_memory_relevance(memory, "recency")
        frequency = memory_manager.calculate_memory_relevance(memory, "frequency")
        confidence = memory_manager.calculate_memory_relevance(memory, "confidence")
        combined = memory_manager.calculate_memory_relevance(memory, "combined")

        # Combined should be weighted: 40% recency, 30% frequency, 30% confidence
        expected = recency * 0.4 + frequency * 0.3 + confidence * 0.3
        assert abs(combined - expected) < 0.01, "Combined score should match weighted formula"

        # Cleanup
        db_session.delete(memory)
        db_session.commit()

    def test_recency_exponential_decay(self, db_session, test_user):
        """Test that recency uses exponential decay"""
        # Create memories at different times
        today = UserProfile(
            user_id=test_user.id,
            category="test",
            key="today",
            value="today",
            confidence=1.0,
            first_mentioned=datetime.now(),
            last_mentioned=datetime.now(),
            mention_count=1
        )

        week_ago = UserProfile(
            user_id=test_user.id,
            category="test",
            key="week_ago",
            value="week ago",
            confidence=1.0,
            first_mentioned=datetime.now() - timedelta(days=7),
            last_mentioned=datetime.now() - timedelta(days=7),
            mention_count=1
        )

        db_session.add_all([today, week_ago])
        db_session.commit()

        today_score = memory_manager.calculate_memory_relevance(today, "recency")
        week_score = memory_manager.calculate_memory_relevance(week_ago, "recency")

        # Today should be close to 100
        assert today_score > 95, "Today's memory should score very high"

        # Week ago should be significantly lower (0.9^7 ≈ 0.48)
        assert week_score < 60, "Week-old memory should score lower"
        assert today_score > week_score, "Today should score higher than week ago"

        # Cleanup
        db_session.delete(today)
        db_session.delete(week_ago)
        db_session.commit()

    def test_frequency_logarithmic_scale(self, db_session, test_user):
        """Test that frequency uses logarithmic scaling"""
        low_freq = UserProfile(
            user_id=test_user.id,
            category="test",
            key="low",
            value="low frequency",
            confidence=1.0,
            first_mentioned=datetime.now(),
            last_mentioned=datetime.now(),
            mention_count=2  # log(3) * 20 ≈ 22
        )

        high_freq = UserProfile(
            user_id=test_user.id,
            category="test",
            key="high",
            value="high frequency",
            confidence=1.0,
            first_mentioned=datetime.now(),
            last_mentioned=datetime.now(),
            mention_count=100  # log(101) * 20 ≈ 92
        )

        db_session.add_all([low_freq, high_freq])
        db_session.commit()

        low_score = memory_manager.calculate_memory_relevance(low_freq, "frequency")
        high_score = memory_manager.calculate_memory_relevance(high_freq, "frequency")

        # Should use logarithmic scale (not linear)
        assert high_score > low_score, "Higher frequency should score higher"
        # With linear scale, high would be 50x higher; with log it's only ~4x
        ratio = high_score / low_score if low_score > 0 else 0
        assert ratio < 10, "Log scale should prevent extreme ratios"

        # Cleanup
        db_session.delete(low_freq)
        db_session.delete(high_freq)
        db_session.commit()


# Pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "ranking: marks tests for relevance ranking feature"
    )
