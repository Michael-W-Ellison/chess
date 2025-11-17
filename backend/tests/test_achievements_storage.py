"""
Test achievements category storage

Run with: pytest backend/tests/test_achievements_storage.py -v
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
    user = User(id=9999, name="AchievementsTestUser")
    db_session.add(user)
    db_session.commit()
    yield user
    # Cleanup
    db_session.query(UserProfile).filter(UserProfile.user_id == user.id).delete()
    db_session.delete(user)
    db_session.commit()


class TestAchievementsStorage:
    """Tests for achievements category storage"""

    def test_add_achievement(self, db_session, test_user):
        """Test adding a new achievement"""
        achievement = memory_manager.add_achievement(
            test_user.id,
            "academic",
            "made honor roll",
            db_session
        )

        assert achievement is not None, "Should create achievement"
        assert achievement.category == "achievement", "Category should be 'achievement'"
        assert achievement.key == "academic", "Key should match"
        assert achievement.value == "made honor roll", "Value should match"
        assert achievement.confidence == 1.0, "User-added achievements should have full confidence"
        assert achievement.mention_count == 1, "Initial mention count should be 1"

        # Cleanup
        db_session.delete(achievement)
        db_session.commit()

    def test_add_duplicate_achievement_updates(self, db_session, test_user):
        """Test that adding a duplicate achievement updates the existing one"""
        # Add first achievement
        achievement1 = memory_manager.add_achievement(
            test_user.id,
            "sports",
            "joined soccer team",
            db_session
        )

        # Add duplicate with different value
        achievement2 = memory_manager.add_achievement(
            test_user.id,
            "sports",
            "made varsity soccer team",
            db_session
        )

        # Should be the same object (updated)
        assert achievement1.id == achievement2.id, "Should update existing achievement"
        assert achievement2.value == "made varsity soccer team", "Value should be updated"
        assert achievement2.mention_count == 2, "Mention count should increment"

        # Cleanup
        db_session.delete(achievement2)
        db_session.commit()

    def test_add_achievement_empty_key_raises_error(self, db_session, test_user):
        """Test that empty key raises ValueError"""
        with pytest.raises(ValueError, match="Key and value cannot be empty"):
            memory_manager.add_achievement(test_user.id, "", "value", db_session)

    def test_add_achievement_empty_value_raises_error(self, db_session, test_user):
        """Test that empty value raises ValueError"""
        with pytest.raises(ValueError, match="Key and value cannot be empty"):
            memory_manager.add_achievement(test_user.id, "key", "", db_session)

    def test_get_achievements(self, db_session, test_user):
        """Test retrieving all achievements for a user"""
        # Add multiple achievements
        a1 = memory_manager.add_achievement(test_user.id, "academic", "perfect attendance", db_session)
        a2 = memory_manager.add_achievement(test_user.id, "sports", "won championship", db_session)
        a3 = memory_manager.add_achievement(test_user.id, "personal", "read 50 books", db_session)

        # Get all achievements
        achievements = memory_manager.get_achievements(test_user.id, db_session)

        assert len(achievements) == 3, "Should return all 3 achievements"

        keys = {a.key for a in achievements}
        assert "academic" in keys, "Should include academic achievement"
        assert "sports" in keys, "Should include sports achievement"
        assert "personal" in keys, "Should include personal achievement"

        # Cleanup
        db_session.delete(a1)
        db_session.delete(a2)
        db_session.delete(a3)
        db_session.commit()

    def test_get_achievements_empty(self, db_session, test_user):
        """Test getting achievements when none exist"""
        achievements = memory_manager.get_achievements(test_user.id, db_session)

        assert isinstance(achievements, list), "Should return a list"
        # May or may not be empty depending on previous test cleanup

    def test_get_achievement_by_id(self, db_session, test_user):
        """Test retrieving a specific achievement by ID"""
        # Add an achievement
        achievement = memory_manager.add_achievement(
            test_user.id,
            "community",
            "volunteered 100 hours",
            db_session
        )

        # Retrieve by ID
        retrieved = memory_manager.get_achievement_by_id(
            achievement.id,
            test_user.id,
            db_session
        )

        assert retrieved is not None, "Should find the achievement"
        assert retrieved.id == achievement.id, "IDs should match"
        assert retrieved.key == "community", "Key should match"
        assert retrieved.value == "volunteered 100 hours", "Value should match"

        # Cleanup
        db_session.delete(achievement)
        db_session.commit()

    def test_get_achievement_by_id_not_found(self, db_session, test_user):
        """Test getting a non-existent achievement"""
        retrieved = memory_manager.get_achievement_by_id(99999, test_user.id, db_session)

        assert retrieved is None, "Should return None for non-existent achievement"

    def test_update_achievement_value(self, db_session, test_user):
        """Test updating an achievement's value"""
        # Add an achievement
        achievement = memory_manager.add_achievement(
            test_user.id,
            "creative",
            "won art contest",
            db_session
        )

        # Update the value
        updated = memory_manager.update_achievement(
            achievement.id,
            test_user.id,
            None,
            "won state art competition",
            db_session
        )

        assert updated is not None, "Should return updated achievement"
        assert updated.value == "won state art competition", "Value should be updated"
        assert updated.key == "creative", "Key should remain unchanged"

        # Cleanup
        db_session.delete(updated)
        db_session.commit()

    def test_update_achievement_key(self, db_session, test_user):
        """Test updating an achievement's key"""
        # Add an achievement
        achievement = memory_manager.add_achievement(
            test_user.id,
            "misc",
            "learned to juggle",
            db_session
        )

        # Update the key
        updated = memory_manager.update_achievement(
            achievement.id,
            test_user.id,
            "skill",
            None,
            db_session
        )

        assert updated is not None, "Should return updated achievement"
        assert updated.key == "skill", "Key should be updated"
        assert updated.value == "learned to juggle", "Value should remain unchanged"

        # Cleanup
        db_session.delete(updated)
        db_session.commit()

    def test_update_achievement_both(self, db_session, test_user):
        """Test updating both key and value"""
        # Add an achievement
        achievement = memory_manager.add_achievement(
            test_user.id,
            "test",
            "test value",
            db_session
        )

        # Update both
        updated = memory_manager.update_achievement(
            achievement.id,
            test_user.id,
            "leadership",
            "became class president",
            db_session
        )

        assert updated is not None, "Should return updated achievement"
        assert updated.key == "leadership", "Key should be updated"
        assert updated.value == "became class president", "Value should be updated"

        # Cleanup
        db_session.delete(updated)
        db_session.commit()

    def test_update_achievement_neither_raises_error(self, db_session, test_user):
        """Test that updating with neither key nor value raises error"""
        # Add an achievement
        achievement = memory_manager.add_achievement(
            test_user.id,
            "test",
            "value",
            db_session
        )

        with pytest.raises(ValueError, match="Must provide at least one"):
            memory_manager.update_achievement(
                achievement.id,
                test_user.id,
                None,
                None,
                db_session
            )

        # Cleanup
        db_session.delete(achievement)
        db_session.commit()

    def test_update_achievement_not_found(self, db_session, test_user):
        """Test updating a non-existent achievement"""
        updated = memory_manager.update_achievement(
            99999,
            test_user.id,
            "key",
            "value",
            db_session
        )

        assert updated is None, "Should return None for non-existent achievement"

    def test_delete_achievement(self, db_session, test_user):
        """Test deleting an achievement"""
        # Add an achievement
        achievement = memory_manager.add_achievement(
            test_user.id,
            "to_delete",
            "temporary achievement",
            db_session
        )

        achievement_id = achievement.id

        # Delete it
        deleted = memory_manager.delete_achievement(
            achievement_id,
            test_user.id,
            db_session
        )

        assert deleted is True, "Should return True on successful deletion"

        # Verify it's gone
        retrieved = memory_manager.get_achievement_by_id(
            achievement_id,
            test_user.id,
            db_session
        )

        assert retrieved is None, "Achievement should no longer exist"

    def test_delete_achievement_not_found(self, db_session, test_user):
        """Test deleting a non-existent achievement"""
        deleted = memory_manager.delete_achievement(99999, test_user.id, db_session)

        assert deleted is False, "Should return False when achievement not found"

    def test_achievements_ordered_by_last_mentioned(self, db_session, test_user):
        """Test that achievements are returned in order of last_mentioned"""
        import time

        # Add achievements with slight time delay
        a1 = memory_manager.add_achievement(test_user.id, "first", "value1", db_session)
        time.sleep(0.1)
        a2 = memory_manager.add_achievement(test_user.id, "second", "value2", db_session)
        time.sleep(0.1)
        a3 = memory_manager.add_achievement(test_user.id, "third", "value3", db_session)

        # Get all achievements
        achievements = memory_manager.get_achievements(test_user.id, db_session)

        # Should be ordered by most recent first
        assert achievements[0].key == "third", "Most recent should be first"
        assert achievements[1].key == "second", "Second most recent should be second"
        assert achievements[2].key == "first", "Oldest should be last"

        # Cleanup
        db_session.delete(a1)
        db_session.delete(a2)
        db_session.delete(a3)
        db_session.commit()

    def test_achievements_isolation_between_users(self, db_session):
        """Test that achievements are isolated between users"""
        # Create two users
        user1 = User(id=10009, name="User1")
        user2 = User(id=10010, name="User2")
        db_session.add_all([user1, user2])
        db_session.commit()

        # Add achievements for each user
        a1 = memory_manager.add_achievement(user1.id, "academic", "user1's achievement", db_session)
        a2 = memory_manager.add_achievement(user2.id, "academic", "user2's achievement", db_session)

        # Get achievements for each user
        user1_achievements = memory_manager.get_achievements(user1.id, db_session)
        user2_achievements = memory_manager.get_achievements(user2.id, db_session)

        # Each user should only see their own achievements
        assert len([a for a in user1_achievements if a.key == "academic"]) == 1, "User1 should have 1 achievement"
        assert len([a for a in user2_achievements if a.key == "academic"]) == 1, "User2 should have 1 achievement"

        user1_academic = [a for a in user1_achievements if a.key == "academic"][0]
        user2_academic = [a for a in user2_achievements if a.key == "academic"][0]

        assert user1_academic.value == "user1's achievement", "User1's achievement should match"
        assert user2_academic.value == "user2's achievement", "User2's achievement should match"

        # Cleanup
        db_session.delete(a1)
        db_session.delete(a2)
        db_session.delete(user1)
        db_session.delete(user2)
        db_session.commit()

    def test_achievements_separate_from_other_categories(self, db_session, test_user):
        """Test that achievements are kept separate from other categories"""
        # Add a goal and achievement with same key
        goal = memory_manager.add_goal(test_user.id, "academic", "get all A's", db_session)
        achievement = memory_manager.add_achievement(test_user.id, "academic", "made honor roll", db_session)

        # Get each category
        goals = memory_manager.get_goals(test_user.id, db_session)
        achievements = memory_manager.get_achievements(test_user.id, db_session)

        # Check they're separate
        goal_academics = [g.value for g in goals if g.key == "academic"]
        achievement_academics = [a.value for a in achievements if a.key == "academic"]

        assert "get all A's" in goal_academics, "Goals should contain goal value"
        assert "made honor roll" in achievement_academics, "Achievements should contain achievement value"
        assert "made honor roll" not in goal_academics, "Goals should not contain achievement value"
        assert "get all A's" not in achievement_academics, "Achievements should not contain goal value"

        # Cleanup
        db_session.delete(goal)
        db_session.delete(achievement)
        db_session.commit()

    def test_various_achievement_types(self, db_session, test_user):
        """Test storing different types of achievements"""
        # Academic
        academic = memory_manager.add_achievement(test_user.id, "academic", "made honor roll", db_session)

        # Sports
        sports = memory_manager.add_achievement(test_user.id, "sports", "won championship", db_session)

        # Personal
        personal = memory_manager.add_achievement(test_user.id, "personal", "read 100 books", db_session)

        # Creative
        creative = memory_manager.add_achievement(test_user.id, "creative", "won art contest", db_session)

        # Community
        community = memory_manager.add_achievement(test_user.id, "community", "volunteered 200 hours", db_session)

        # Get all achievements
        achievements = memory_manager.get_achievements(test_user.id, db_session)

        assert len(achievements) == 5, "Should have 5 different achievements"

        keys = {a.key for a in achievements}
        assert "academic" in keys
        assert "sports" in keys
        assert "personal" in keys
        assert "creative" in keys
        assert "community" in keys

        # Cleanup
        for achievement in [academic, sports, personal, creative, community]:
            db_session.delete(achievement)
        db_session.commit()


# Pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "achievements: marks tests for achievements storage feature"
    )
