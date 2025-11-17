"""
Test keyword-based memory search

Run with: pytest backend/tests/test_memory_search.py -v
"""

import pytest
import sys
import os

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
    user = User(id=9996, name="SearchTestUser")
    db_session.add(user)
    db_session.commit()
    yield user
    # Cleanup
    db_session.query(UserProfile).filter(UserProfile.user_id == user.id).delete()
    db_session.delete(user)
    db_session.commit()


@pytest.fixture(scope="module")
def sample_memories(db_session, test_user):
    """Create sample memories for testing search"""
    memories = []

    # Favorites
    memories.append(memory_manager.add_favorite(test_user.id, "color", "blue", db_session))
    memories.append(memory_manager.add_favorite(test_user.id, "food", "pizza", db_session))
    memories.append(memory_manager.add_favorite(test_user.id, "sport", "soccer", db_session))

    # Dislikes
    memories.append(memory_manager.add_dislike(test_user.id, "vegetable", "broccoli", db_session))
    memories.append(memory_manager.add_dislike(test_user.id, "activity", "running", db_session))

    # People
    memories.append(memory_manager.add_person(test_user.id, "friend_emma", "best friend who loves soccer", db_session))
    memories.append(memory_manager.add_person(test_user.id, "teacher_smith", "math teacher", db_session))

    # Goals
    memories.append(memory_manager.add_goal(test_user.id, "academic", "get all A's this semester", db_session))
    memories.append(memory_manager.add_goal(test_user.id, "sports", "make the soccer team", db_session))

    # Achievements
    memories.append(memory_manager.add_achievement(test_user.id, "academic", "made honor roll", db_session))
    memories.append(memory_manager.add_achievement(test_user.id, "sports", "won soccer championship", db_session))

    yield memories

    # Cleanup
    for memory in memories:
        db_session.delete(memory)
    db_session.commit()


class TestMemorySearch:
    """Tests for keyword-based memory search"""

    def test_search_single_keyword(self, db_session, test_user, sample_memories):
        """Test searching with a single keyword"""
        results = memory_manager.search_memories(
            user_id=test_user.id,
            keywords="soccer",
            db=db_session
        )

        assert len(results) > 0, "Should find results for 'soccer'"

        # Should find sport favorite, person (Emma loves soccer), goal, and achievement
        result_values = [r.value for r in results]
        assert any("soccer" in v.lower() for v in result_values), "Should contain soccer-related memories"

    def test_search_multiple_keywords(self, db_session, test_user, sample_memories):
        """Test searching with multiple keywords"""
        results = memory_manager.search_memories(
            user_id=test_user.id,
            keywords="soccer team",
            db=db_session
        )

        assert len(results) > 0, "Should find results for 'soccer team'"

        # Should find memories containing either 'soccer' or 'team'
        result_text = " ".join([r.key + " " + r.value for r in results]).lower()
        assert "soccer" in result_text or "team" in result_text

    def test_search_case_insensitive(self, db_session, test_user, sample_memories):
        """Test that search is case insensitive"""
        results_lower = memory_manager.search_memories(
            user_id=test_user.id,
            keywords="soccer",
            db=db_session
        )

        results_upper = memory_manager.search_memories(
            user_id=test_user.id,
            keywords="SOCCER",
            db=db_session
        )

        results_mixed = memory_manager.search_memories(
            user_id=test_user.id,
            keywords="SoCcEr",
            db=db_session
        )

        # All should return the same results
        assert len(results_lower) == len(results_upper) == len(results_mixed)

    def test_search_with_category_filter(self, db_session, test_user, sample_memories):
        """Test searching with category filter"""
        # Search only in favorites
        results = memory_manager.search_memories(
            user_id=test_user.id,
            keywords="soccer",
            db=db_session,
            category="favorite"
        )

        assert len(results) > 0, "Should find soccer in favorites"
        assert all(r.category == "favorite" for r in results), "All results should be favorites"

    def test_search_in_goals_category(self, db_session, test_user, sample_memories):
        """Test searching in goals category"""
        results = memory_manager.search_memories(
            user_id=test_user.id,
            keywords="academic",
            db=db_session,
            category="goal"
        )

        assert len(results) > 0, "Should find academic goal"
        assert all(r.category == "goal" for r in results), "All results should be goals"

    def test_search_in_people_category(self, db_session, test_user, sample_memories):
        """Test searching in people category"""
        results = memory_manager.search_memories(
            user_id=test_user.id,
            keywords="emma",
            db=db_session,
            category="person"
        )

        assert len(results) > 0, "Should find Emma"
        assert all(r.category == "person" for r in results), "All results should be people"

    def test_search_partial_match(self, db_session, test_user, sample_memories):
        """Test that partial matches work"""
        results = memory_manager.search_memories(
            user_id=test_user.id,
            keywords="socc",  # Partial match for soccer
            db=db_session
        )

        assert len(results) > 0, "Should find results with partial match"

    def test_search_with_limit(self, db_session, test_user, sample_memories):
        """Test that limit parameter works"""
        # Search with low limit
        results = memory_manager.search_memories(
            user_id=test_user.id,
            keywords="a",  # Common letter that should match many memories
            db=db_session,
            limit=2
        )

        assert len(results) <= 2, "Should respect limit parameter"

    def test_search_empty_keywords(self, db_session, test_user, sample_memories):
        """Test searching with empty keywords"""
        results = memory_manager.search_memories(
            user_id=test_user.id,
            keywords="",
            db=db_session
        )

        assert len(results) == 0, "Empty keywords should return no results"

    def test_search_whitespace_only(self, db_session, test_user, sample_memories):
        """Test searching with whitespace only"""
        results = memory_manager.search_memories(
            user_id=test_user.id,
            keywords="   ",
            db=db_session
        )

        assert len(results) == 0, "Whitespace-only keywords should return no results"

    def test_search_no_matches(self, db_session, test_user, sample_memories):
        """Test searching with keywords that don't match anything"""
        results = memory_manager.search_memories(
            user_id=test_user.id,
            keywords="xyzabc123",
            db=db_session
        )

        assert len(results) == 0, "Non-matching keywords should return no results"

    def test_search_ranking_exact_match_higher(self, db_session, test_user):
        """Test that exact matches rank higher than partial matches"""
        # Create specific memories for this test
        exact = memory_manager.add_favorite(test_user.id, "blue", "my favorite color", db_session)
        partial = memory_manager.add_favorite(test_user.id, "blueberry", "good snack", db_session)

        results = memory_manager.search_memories(
            user_id=test_user.id,
            keywords="blue",
            db=db_session
        )

        # Exact match should rank higher
        assert len(results) >= 2, "Should find both memories"
        assert results[0].key == "blue", "Exact match should rank first"

        # Cleanup
        db_session.delete(exact)
        db_session.delete(partial)
        db_session.commit()

    def test_search_by_category_name(self, db_session, test_user, sample_memories):
        """Test searching by category name as keyword"""
        results = memory_manager.search_memories(
            user_id=test_user.id,
            keywords="favorite",
            db=db_session
        )

        # Should find favorites (category matches)
        assert len(results) > 0, "Should find memories by category name"
        assert any(r.category == "favorite" for r in results), "Should include favorites"

    def test_search_user_isolation(self, db_session):
        """Test that search results are isolated by user"""
        # Create two users
        user1 = User(id=10011, name="User1")
        user2 = User(id=10012, name="User2")
        db_session.add_all([user1, user2])
        db_session.commit()

        # Add memories for each user
        m1 = memory_manager.add_favorite(user1.id, "sport", "basketball", db_session)
        m2 = memory_manager.add_favorite(user2.id, "sport", "tennis", db_session)

        # Search for each user
        user1_results = memory_manager.search_memories(user1.id, "sport", db_session)
        user2_results = memory_manager.search_memories(user2.id, "sport", db_session)

        # Each user should only see their own results
        user1_values = [r.value for r in user1_results]
        user2_values = [r.value for r in user2_results]

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

    def test_search_multiple_categories(self, db_session, test_user, sample_memories):
        """Test that search works across multiple categories when no filter applied"""
        results = memory_manager.search_memories(
            user_id=test_user.id,
            keywords="academic",
            db=db_session
        )

        # Should find both goal and achievement with 'academic'
        categories = {r.category for r in results}
        assert "goal" in categories, "Should find goal"
        assert "achievement" in categories, "Should find achievement"

    def test_relevance_scoring(self, db_session, test_user):
        """Test that relevance scoring prioritizes better matches"""
        # Create memories with different match qualities
        high = memory_manager.add_favorite(test_user.id, "math", "math is great", db_session)
        medium = memory_manager.add_favorite(test_user.id, "school", "I love math class", db_session)
        low = memory_manager.add_favorite(test_user.id, "games", "mathematic puzzles", db_session)

        results = memory_manager.search_memories(
            user_id=test_user.id,
            keywords="math",
            db=db_session
        )

        # Should rank in order of relevance
        assert len(results) >= 3, "Should find all three memories"

        # The one with 'math' as key and exact word in value should rank highest
        assert results[0].id == high.id, "Exact key match with word match in value should rank first"

        # Cleanup
        db_session.delete(high)
        db_session.delete(medium)
        db_session.delete(low)
        db_session.commit()


# Pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "search: marks tests for memory search feature"
    )
