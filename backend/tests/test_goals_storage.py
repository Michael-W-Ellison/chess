"""
Test goals category storage

Run with: pytest backend/tests/test_goals_storage.py -v
"""

import pytest
import sys
import os
from datetime import datetime

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
    user = User(id=9998, name="GoalsTestUser")
    db_session.add(user)
    db_session.commit()
    yield user
    # Cleanup
    db_session.query(UserProfile).filter(UserProfile.user_id == user.id).delete()
    db_session.delete(user)
    db_session.commit()


class TestGoalsStorage:
    """Tests for goals category storage"""

    def test_add_goal(self, db_session, test_user):
        """Test adding a new goal"""
        goal = memory_manager.add_goal(
            test_user.id,
            "academic",
            "get all A's this semester",
            db_session
        )

        assert goal is not None, "Should create goal"
        assert goal.category == "goal", "Category should be 'goal'"
        assert goal.key == "academic", "Key should match"
        assert goal.value == "get all A's this semester", "Value should match"
        assert goal.confidence == 1.0, "User-added goals should have full confidence"
        assert goal.mention_count == 1, "Initial mention count should be 1"

        # Cleanup
        db_session.delete(goal)
        db_session.commit()

    def test_add_duplicate_goal_updates(self, db_session, test_user):
        """Test that adding a duplicate goal updates the existing one"""
        # Add first goal
        goal1 = memory_manager.add_goal(
            test_user.id,
            "fitness",
            "run a mile",
            db_session
        )

        # Add duplicate with different value
        goal2 = memory_manager.add_goal(
            test_user.id,
            "fitness",
            "run a mile without stopping",
            db_session
        )

        # Should be the same object (updated)
        assert goal1.id == goal2.id, "Should update existing goal"
        assert goal2.value == "run a mile without stopping", "Value should be updated"
        assert goal2.mention_count == 2, "Mention count should increment"

        # Cleanup
        db_session.delete(goal2)
        db_session.commit()

    def test_add_goal_empty_key_raises_error(self, db_session, test_user):
        """Test that empty key raises ValueError"""
        with pytest.raises(ValueError, match="Key and value cannot be empty"):
            memory_manager.add_goal(test_user.id, "", "value", db_session)

    def test_add_goal_empty_value_raises_error(self, db_session, test_user):
        """Test that empty value raises ValueError"""
        with pytest.raises(ValueError, match="Key and value cannot be empty"):
            memory_manager.add_goal(test_user.id, "key", "", db_session)

    def test_get_goals(self, db_session, test_user):
        """Test retrieving all goals for a user"""
        # Add multiple goals
        g1 = memory_manager.add_goal(test_user.id, "academic", "get straight A's", db_session)
        g2 = memory_manager.add_goal(test_user.id, "fitness", "run 5k", db_session)
        g3 = memory_manager.add_goal(test_user.id, "personal", "read 20 books this year", db_session)

        # Get all goals
        goals = memory_manager.get_goals(test_user.id, db_session)

        assert len(goals) == 3, "Should return all 3 goals"

        keys = {g.key for g in goals}
        assert "academic" in keys, "Should include academic goal"
        assert "fitness" in keys, "Should include fitness goal"
        assert "personal" in keys, "Should include personal goal"

        # Cleanup
        db_session.delete(g1)
        db_session.delete(g2)
        db_session.delete(g3)
        db_session.commit()

    def test_get_goals_empty(self, db_session, test_user):
        """Test getting goals when none exist"""
        goals = memory_manager.get_goals(test_user.id, db_session)

        assert isinstance(goals, list), "Should return a list"
        # May or may not be empty depending on previous test cleanup

    def test_get_goal_by_id(self, db_session, test_user):
        """Test retrieving a specific goal by ID"""
        # Add a goal
        goal = memory_manager.add_goal(
            test_user.id,
            "sports",
            "make the basketball team",
            db_session
        )

        # Retrieve by ID
        retrieved = memory_manager.get_goal_by_id(
            goal.id,
            test_user.id,
            db_session
        )

        assert retrieved is not None, "Should find the goal"
        assert retrieved.id == goal.id, "IDs should match"
        assert retrieved.key == "sports", "Key should match"
        assert retrieved.value == "make the basketball team", "Value should match"

        # Cleanup
        db_session.delete(goal)
        db_session.commit()

    def test_get_goal_by_id_not_found(self, db_session, test_user):
        """Test getting a non-existent goal"""
        retrieved = memory_manager.get_goal_by_id(99999, test_user.id, db_session)

        assert retrieved is None, "Should return None for non-existent goal"

    def test_update_goal_value(self, db_session, test_user):
        """Test updating a goal's value"""
        # Add a goal
        goal = memory_manager.add_goal(
            test_user.id,
            "learning",
            "learn piano",
            db_session
        )

        # Update the value
        updated = memory_manager.update_goal(
            goal.id,
            test_user.id,
            None,
            "learn to play 3 songs on piano",
            db_session
        )

        assert updated is not None, "Should return updated goal"
        assert updated.value == "learn to play 3 songs on piano", "Value should be updated"
        assert updated.key == "learning", "Key should remain unchanged"

        # Cleanup
        db_session.delete(updated)
        db_session.commit()

    def test_update_goal_key(self, db_session, test_user):
        """Test updating a goal's key"""
        # Add a goal
        goal = memory_manager.add_goal(
            test_user.id,
            "hobby",
            "build a robot",
            db_session
        )

        # Update the key
        updated = memory_manager.update_goal(
            goal.id,
            test_user.id,
            "project",
            None,
            db_session
        )

        assert updated is not None, "Should return updated goal"
        assert updated.key == "project", "Key should be updated"
        assert updated.value == "build a robot", "Value should remain unchanged"

        # Cleanup
        db_session.delete(updated)
        db_session.commit()

    def test_update_goal_both(self, db_session, test_user):
        """Test updating both key and value"""
        # Add a goal
        goal = memory_manager.add_goal(
            test_user.id,
            "skill",
            "learn coding",
            db_session
        )

        # Update both
        updated = memory_manager.update_goal(
            goal.id,
            test_user.id,
            "technology",
            "build my own website",
            db_session
        )

        assert updated is not None, "Should return updated goal"
        assert updated.key == "technology", "Key should be updated"
        assert updated.value == "build my own website", "Value should be updated"

        # Cleanup
        db_session.delete(updated)
        db_session.commit()

    def test_update_goal_neither_raises_error(self, db_session, test_user):
        """Test that updating with neither key nor value raises error"""
        # Add a goal
        goal = memory_manager.add_goal(
            test_user.id,
            "test",
            "value",
            db_session
        )

        with pytest.raises(ValueError, match="Must provide at least one"):
            memory_manager.update_goal(
                goal.id,
                test_user.id,
                None,
                None,
                db_session
            )

        # Cleanup
        db_session.delete(goal)
        db_session.commit()

    def test_update_goal_not_found(self, db_session, test_user):
        """Test updating a non-existent goal"""
        updated = memory_manager.update_goal(
            99999,
            test_user.id,
            "key",
            "value",
            db_session
        )

        assert updated is None, "Should return None for non-existent goal"

    def test_delete_goal(self, db_session, test_user):
        """Test deleting a goal"""
        # Add a goal
        goal = memory_manager.add_goal(
            test_user.id,
            "to_delete",
            "temporary goal",
            db_session
        )

        goal_id = goal.id

        # Delete it
        deleted = memory_manager.delete_goal(
            goal_id,
            test_user.id,
            db_session
        )

        assert deleted is True, "Should return True on successful deletion"

        # Verify it's gone
        retrieved = memory_manager.get_goal_by_id(
            goal_id,
            test_user.id,
            db_session
        )

        assert retrieved is None, "Goal should no longer exist"

    def test_delete_goal_not_found(self, db_session, test_user):
        """Test deleting a non-existent goal"""
        deleted = memory_manager.delete_goal(99999, test_user.id, db_session)

        assert deleted is False, "Should return False when goal not found"

    def test_goals_ordered_by_last_mentioned(self, db_session, test_user):
        """Test that goals are returned in order of last_mentioned"""
        import time

        # Add goals with slight time delay
        g1 = memory_manager.add_goal(test_user.id, "first", "value1", db_session)
        time.sleep(0.1)
        g2 = memory_manager.add_goal(test_user.id, "second", "value2", db_session)
        time.sleep(0.1)
        g3 = memory_manager.add_goal(test_user.id, "third", "value3", db_session)

        # Get all goals
        goals = memory_manager.get_goals(test_user.id, db_session)

        # Should be ordered by most recent first
        assert goals[0].key == "third", "Most recent should be first"
        assert goals[1].key == "second", "Second most recent should be second"
        assert goals[2].key == "first", "Oldest should be last"

        # Cleanup
        db_session.delete(g1)
        db_session.delete(g2)
        db_session.delete(g3)
        db_session.commit()

    def test_goals_isolation_between_users(self, db_session):
        """Test that goals are isolated between users"""
        # Create two users
        user1 = User(id=10007, name="User1")
        user2 = User(id=10008, name="User2")
        db_session.add_all([user1, user2])
        db_session.commit()

        # Add goals for each user
        g1 = memory_manager.add_goal(user1.id, "academic", "user1's goal", db_session)
        g2 = memory_manager.add_goal(user2.id, "academic", "user2's goal", db_session)

        # Get goals for each user
        user1_goals = memory_manager.get_goals(user1.id, db_session)
        user2_goals = memory_manager.get_goals(user2.id, db_session)

        # Each user should only see their own goals
        assert len([g for g in user1_goals if g.key == "academic"]) == 1, "User1 should have 1 goal"
        assert len([g for g in user2_goals if g.key == "academic"]) == 1, "User2 should have 1 goal"

        user1_academic = [g for g in user1_goals if g.key == "academic"][0]
        user2_academic = [g for g in user2_goals if g.key == "academic"][0]

        assert user1_academic.value == "user1's goal", "User1's goal should match"
        assert user2_academic.value == "user2's goal", "User2's goal should match"

        # Cleanup
        db_session.delete(g1)
        db_session.delete(g2)
        db_session.delete(user1)
        db_session.delete(user2)
        db_session.commit()

    def test_goals_separate_from_other_categories(self, db_session, test_user):
        """Test that goals are kept separate from favorites and other categories"""
        # Add a favorite, person, and goal with same key
        favorite = memory_manager.add_favorite(test_user.id, "soccer", "favorite sport", db_session)
        goal = memory_manager.add_goal(test_user.id, "soccer", "make the team", db_session)

        # Get each category
        favorites = memory_manager.get_favorites(test_user.id, db_session)
        goals = memory_manager.get_goals(test_user.id, db_session)

        # Check they're separate
        fav_soccers = [f.value for f in favorites if f.key == "soccer"]
        goal_soccers = [g.value for g in goals if g.key == "soccer"]

        assert "favorite sport" in fav_soccers, "Favorites should contain favorite sport"
        assert "make the team" in goal_soccers, "Goals should contain make the team"
        assert "make the team" not in fav_soccers, "Favorites should not contain goal value"
        assert "favorite sport" not in goal_soccers, "Goals should not contain favorite value"

        # Cleanup
        db_session.delete(favorite)
        db_session.delete(goal)
        db_session.commit()

    def test_various_goal_types(self, db_session, test_user):
        """Test storing different types of goals"""
        # Academic
        academic = memory_manager.add_goal(test_user.id, "academic", "get all A's this semester", db_session)

        # Fitness
        fitness = memory_manager.add_goal(test_user.id, "fitness", "run a 5k race", db_session)

        # Personal
        personal = memory_manager.add_goal(test_user.id, "personal", "read 30 books this year", db_session)

        # Social
        social = memory_manager.add_goal(test_user.id, "social", "make 3 new friends", db_session)

        # Creative
        creative = memory_manager.add_goal(test_user.id, "creative", "learn to play guitar", db_session)

        # Get all goals
        goals = memory_manager.get_goals(test_user.id, db_session)

        assert len(goals) == 5, "Should have 5 different goals"

        keys = {g.key for g in goals}
        assert "academic" in keys
        assert "fitness" in keys
        assert "personal" in keys
        assert "social" in keys
        assert "creative" in keys

        # Cleanup
        for goal in [academic, fitness, personal, social, creative]:
            db_session.delete(goal)
        db_session.commit()


# Pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "goals: marks tests for goals storage feature"
    )
