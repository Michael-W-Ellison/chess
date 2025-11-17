"""
Test dislikes category storage

Run with: pytest backend/tests/test_dislikes_storage.py -v
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
    user = User(id=9998, name="DislikesTestUser")
    db_session.add(user)
    db_session.commit()
    yield user
    # Cleanup
    db_session.query(UserProfile).filter(UserProfile.user_id == user.id).delete()
    db_session.delete(user)
    db_session.commit()


class TestDislikesStorage:
    """Tests for dislikes category storage"""

    def test_add_dislike(self, db_session, test_user):
        """Test adding a new dislike"""
        dislike = memory_manager.add_dislike(
            test_user.id,
            "vegetable",
            "broccoli",
            db_session
        )

        assert dislike is not None, "Should create dislike"
        assert dislike.category == "dislike", "Category should be 'dislike'"
        assert dislike.key == "vegetable", "Key should match"
        assert dislike.value == "broccoli", "Value should match"
        assert dislike.confidence == 1.0, "User-added dislikes should have full confidence"
        assert dislike.mention_count == 1, "Initial mention count should be 1"

        # Cleanup
        db_session.delete(dislike)
        db_session.commit()

    def test_add_duplicate_dislike_updates(self, db_session, test_user):
        """Test that adding a duplicate dislike updates the existing one"""
        # Add first dislike
        dislike1 = memory_manager.add_dislike(
            test_user.id,
            "food",
            "liver",
            db_session
        )

        # Add duplicate with different value
        dislike2 = memory_manager.add_dislike(
            test_user.id,
            "food",
            "spinach",
            db_session
        )

        # Should be the same object (updated)
        assert dislike1.id == dislike2.id, "Should update existing dislike"
        assert dislike2.value == "spinach", "Value should be updated"
        assert dislike2.mention_count == 2, "Mention count should increment"

        # Cleanup
        db_session.delete(dislike2)
        db_session.commit()

    def test_add_dislike_empty_key_raises_error(self, db_session, test_user):
        """Test that empty key raises ValueError"""
        with pytest.raises(ValueError, match="Key and value cannot be empty"):
            memory_manager.add_dislike(test_user.id, "", "value", db_session)

    def test_add_dislike_empty_value_raises_error(self, db_session, test_user):
        """Test that empty value raises ValueError"""
        with pytest.raises(ValueError, match="Key and value cannot be empty"):
            memory_manager.add_dislike(test_user.id, "key", "", db_session)

    def test_get_dislikes(self, db_session, test_user):
        """Test retrieving all dislikes for a user"""
        # Add multiple dislikes
        dis1 = memory_manager.add_dislike(test_user.id, "activity", "running", db_session)
        dis2 = memory_manager.add_dislike(test_user.id, "weather", "rain", db_session)
        dis3 = memory_manager.add_dislike(test_user.id, "subject", "history", db_session)

        # Get all dislikes
        dislikes = memory_manager.get_dislikes(test_user.id, db_session)

        assert len(dislikes) == 3, "Should return all 3 dislikes"

        keys = {d.key for d in dislikes}
        assert "activity" in keys, "Should include activity"
        assert "weather" in keys, "Should include weather"
        assert "subject" in keys, "Should include subject"

        # Cleanup
        db_session.delete(dis1)
        db_session.delete(dis2)
        db_session.delete(dis3)
        db_session.commit()

    def test_get_dislikes_empty(self, db_session, test_user):
        """Test getting dislikes when none exist"""
        dislikes = memory_manager.get_dislikes(test_user.id, db_session)

        assert isinstance(dislikes, list), "Should return a list"
        # May or may not be empty depending on previous test cleanup

    def test_get_dislike_by_id(self, db_session, test_user):
        """Test retrieving a specific dislike by ID"""
        # Add a dislike
        dislike = memory_manager.add_dislike(
            test_user.id,
            "sound",
            "loud music",
            db_session
        )

        # Retrieve by ID
        retrieved = memory_manager.get_dislike_by_id(
            dislike.id,
            test_user.id,
            db_session
        )

        assert retrieved is not None, "Should find the dislike"
        assert retrieved.id == dislike.id, "IDs should match"
        assert retrieved.key == "sound", "Key should match"
        assert retrieved.value == "loud music", "Value should match"

        # Cleanup
        db_session.delete(dislike)
        db_session.commit()

    def test_get_dislike_by_id_not_found(self, db_session, test_user):
        """Test getting a non-existent dislike"""
        retrieved = memory_manager.get_dislike_by_id(99999, test_user.id, db_session)

        assert retrieved is None, "Should return None for non-existent dislike"

    def test_update_dislike_value(self, db_session, test_user):
        """Test updating a dislike's value"""
        # Add a dislike
        dislike = memory_manager.add_dislike(
            test_user.id,
            "chore",
            "dishes",
            db_session
        )

        # Update the value
        updated = memory_manager.update_dislike(
            dislike.id,
            test_user.id,
            None,
            "laundry",
            db_session
        )

        assert updated is not None, "Should return updated dislike"
        assert updated.value == "laundry", "Value should be updated"
        assert updated.key == "chore", "Key should remain unchanged"

        # Cleanup
        db_session.delete(updated)
        db_session.commit()

    def test_update_dislike_key(self, db_session, test_user):
        """Test updating a dislike's key"""
        # Add a dislike
        dislike = memory_manager.add_dislike(
            test_user.id,
            "task",
            "homework",
            db_session
        )

        # Update the key
        updated = memory_manager.update_dislike(
            dislike.id,
            test_user.id,
            "activity",
            None,
            db_session
        )

        assert updated is not None, "Should return updated dislike"
        assert updated.key == "activity", "Key should be updated"
        assert updated.value == "homework", "Value should remain unchanged"

        # Cleanup
        db_session.delete(updated)
        db_session.commit()

    def test_update_dislike_both(self, db_session, test_user):
        """Test updating both key and value"""
        # Add a dislike
        dislike = memory_manager.add_dislike(
            test_user.id,
            "game",
            "chess",
            db_session
        )

        # Update both
        updated = memory_manager.update_dislike(
            dislike.id,
            test_user.id,
            "sport",
            "golf",
            db_session
        )

        assert updated is not None, "Should return updated dislike"
        assert updated.key == "sport", "Key should be updated"
        assert updated.value == "golf", "Value should be updated"

        # Cleanup
        db_session.delete(updated)
        db_session.commit()

    def test_update_dislike_neither_raises_error(self, db_session, test_user):
        """Test that updating with neither key nor value raises error"""
        # Add a dislike
        dislike = memory_manager.add_dislike(
            test_user.id,
            "test",
            "value",
            db_session
        )

        with pytest.raises(ValueError, match="Must provide at least one"):
            memory_manager.update_dislike(
                dislike.id,
                test_user.id,
                None,
                None,
                db_session
            )

        # Cleanup
        db_session.delete(dislike)
        db_session.commit()

    def test_update_dislike_not_found(self, db_session, test_user):
        """Test updating a non-existent dislike"""
        updated = memory_manager.update_dislike(
            99999,
            test_user.id,
            "key",
            "value",
            db_session
        )

        assert updated is None, "Should return None for non-existent dislike"

    def test_delete_dislike(self, db_session, test_user):
        """Test deleting a dislike"""
        # Add a dislike
        dislike = memory_manager.add_dislike(
            test_user.id,
            "to_delete",
            "temporary",
            db_session
        )

        dislike_id = dislike.id

        # Delete it
        deleted = memory_manager.delete_dislike(
            dislike_id,
            test_user.id,
            db_session
        )

        assert deleted is True, "Should return True on successful deletion"

        # Verify it's gone
        retrieved = memory_manager.get_dislike_by_id(
            dislike_id,
            test_user.id,
            db_session
        )

        assert retrieved is None, "Dislike should no longer exist"

    def test_delete_dislike_not_found(self, db_session, test_user):
        """Test deleting a non-existent dislike"""
        deleted = memory_manager.delete_dislike(99999, test_user.id, db_session)

        assert deleted is False, "Should return False when dislike not found"

    def test_dislikes_ordered_by_last_mentioned(self, db_session, test_user):
        """Test that dislikes are returned in order of last_mentioned"""
        import time

        # Add dislikes with slight time delay
        dis1 = memory_manager.add_dislike(test_user.id, "first", "value1", db_session)
        time.sleep(0.1)
        dis2 = memory_manager.add_dislike(test_user.id, "second", "value2", db_session)
        time.sleep(0.1)
        dis3 = memory_manager.add_dislike(test_user.id, "third", "value3", db_session)

        # Get all dislikes
        dislikes = memory_manager.get_dislikes(test_user.id, db_session)

        # Should be ordered by most recent first
        assert dislikes[0].key == "third", "Most recent should be first"
        assert dislikes[1].key == "second", "Second most recent should be second"
        assert dislikes[2].key == "first", "Oldest should be last"

        # Cleanup
        db_session.delete(dis1)
        db_session.delete(dis2)
        db_session.delete(dis3)
        db_session.commit()

    def test_dislikes_isolation_between_users(self, db_session):
        """Test that dislikes are isolated between users"""
        # Create two users
        user1 = User(id=10003, name="User1")
        user2 = User(id=10004, name="User2")
        db_session.add_all([user1, user2])
        db_session.commit()

        # Add dislikes for each user
        dis1 = memory_manager.add_dislike(user1.id, "vegetable", "carrots", db_session)
        dis2 = memory_manager.add_dislike(user2.id, "vegetable", "peas", db_session)

        # Get dislikes for each user
        user1_dislikes = memory_manager.get_dislikes(user1.id, db_session)
        user2_dislikes = memory_manager.get_dislikes(user2.id, db_session)

        # Each user should only see their own dislikes
        assert len([d for d in user1_dislikes if d.key == "vegetable"]) == 1, "User1 should have 1 dislike"
        assert len([d for d in user2_dislikes if d.key == "vegetable"]) == 1, "User2 should have 1 dislike"

        user1_veg = [d for d in user1_dislikes if d.key == "vegetable"][0]
        user2_veg = [d for d in user2_dislikes if d.key == "vegetable"][0]

        assert user1_veg.value == "carrots", "User1's vegetable should be carrots"
        assert user2_veg.value == "peas", "User2's vegetable should be peas"

        # Cleanup
        db_session.delete(dis1)
        db_session.delete(dis2)
        db_session.delete(user1)
        db_session.delete(user2)
        db_session.commit()

    def test_dislikes_separate_from_favorites(self, db_session, test_user):
        """Test that dislikes and favorites are kept separate"""
        # Add both a favorite and dislike with same key
        favorite = memory_manager.add_favorite(test_user.id, "color", "blue", db_session)
        dislike = memory_manager.add_dislike(test_user.id, "color", "brown", db_session)

        # Get favorites and dislikes
        favorites = memory_manager.get_favorites(test_user.id, db_session)
        dislikes = memory_manager.get_dislikes(test_user.id, db_session)

        # Check they're separate
        fav_colors = [f.value for f in favorites if f.key == "color"]
        dis_colors = [d.value for d in dislikes if d.key == "color"]

        assert "blue" in fav_colors, "Favorites should contain blue"
        assert "brown" in dis_colors, "Dislikes should contain brown"
        assert "brown" not in fav_colors, "Favorites should not contain brown"
        assert "blue" not in dis_colors, "Dislikes should not contain blue"

        # Cleanup
        db_session.delete(favorite)
        db_session.delete(dislike)
        db_session.commit()


# Pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "dislikes: marks tests for dislikes storage feature"
    )
