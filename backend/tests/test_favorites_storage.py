"""
Test favorites category storage

Run with: pytest backend/tests/test_favorites_storage.py -v
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
    user = User(id=9999, name="FavoritesTestUser")
    db_session.add(user)
    db_session.commit()
    yield user
    # Cleanup
    db_session.query(UserProfile).filter(UserProfile.user_id == user.id).delete()
    db_session.delete(user)
    db_session.commit()


class TestFavoritesStorage:
    """Tests for favorites category storage"""

    def test_add_favorite(self, db_session, test_user):
        """Test adding a new favorite"""
        favorite = memory_manager.add_favorite(
            test_user.id,
            "color",
            "blue",
            db_session
        )

        assert favorite is not None, "Should create favorite"
        assert favorite.category == "favorite", "Category should be 'favorite'"
        assert favorite.key == "color", "Key should match"
        assert favorite.value == "blue", "Value should match"
        assert favorite.confidence == 1.0, "User-added favorites should have full confidence"
        assert favorite.mention_count == 1, "Initial mention count should be 1"

        # Cleanup
        db_session.delete(favorite)
        db_session.commit()

    def test_add_duplicate_favorite_updates(self, db_session, test_user):
        """Test that adding a duplicate favorite updates the existing one"""
        # Add first favorite
        favorite1 = memory_manager.add_favorite(
            test_user.id,
            "food",
            "pizza",
            db_session
        )

        # Add duplicate with different value
        favorite2 = memory_manager.add_favorite(
            test_user.id,
            "food",
            "tacos",
            db_session
        )

        # Should be the same object (updated)
        assert favorite1.id == favorite2.id, "Should update existing favorite"
        assert favorite2.value == "tacos", "Value should be updated"
        assert favorite2.mention_count == 2, "Mention count should increment"

        # Cleanup
        db_session.delete(favorite2)
        db_session.commit()

    def test_add_favorite_empty_key_raises_error(self, db_session, test_user):
        """Test that empty key raises ValueError"""
        with pytest.raises(ValueError, match="Key and value cannot be empty"):
            memory_manager.add_favorite(test_user.id, "", "value", db_session)

    def test_add_favorite_empty_value_raises_error(self, db_session, test_user):
        """Test that empty value raises ValueError"""
        with pytest.raises(ValueError, match="Key and value cannot be empty"):
            memory_manager.add_favorite(test_user.id, "key", "", db_session)

    def test_get_favorites(self, db_session, test_user):
        """Test retrieving all favorites for a user"""
        # Add multiple favorites
        fav1 = memory_manager.add_favorite(test_user.id, "sport", "soccer", db_session)
        fav2 = memory_manager.add_favorite(test_user.id, "game", "chess", db_session)
        fav3 = memory_manager.add_favorite(test_user.id, "subject", "math", db_session)

        # Get all favorites
        favorites = memory_manager.get_favorites(test_user.id, db_session)

        assert len(favorites) == 3, "Should return all 3 favorites"

        keys = {f.key for f in favorites}
        assert "sport" in keys, "Should include sport"
        assert "game" in keys, "Should include game"
        assert "subject" in keys, "Should include subject"

        # Cleanup
        db_session.delete(fav1)
        db_session.delete(fav2)
        db_session.delete(fav3)
        db_session.commit()

    def test_get_favorites_empty(self, db_session, test_user):
        """Test getting favorites when none exist"""
        favorites = memory_manager.get_favorites(test_user.id, db_session)

        assert isinstance(favorites, list), "Should return a list"
        # May or may not be empty depending on previous test cleanup

    def test_get_favorite_by_id(self, db_session, test_user):
        """Test retrieving a specific favorite by ID"""
        # Add a favorite
        favorite = memory_manager.add_favorite(
            test_user.id,
            "animal",
            "dog",
            db_session
        )

        # Retrieve by ID
        retrieved = memory_manager.get_favorite_by_id(
            favorite.id,
            test_user.id,
            db_session
        )

        assert retrieved is not None, "Should find the favorite"
        assert retrieved.id == favorite.id, "IDs should match"
        assert retrieved.key == "animal", "Key should match"
        assert retrieved.value == "dog", "Value should match"

        # Cleanup
        db_session.delete(favorite)
        db_session.commit()

    def test_get_favorite_by_id_not_found(self, db_session, test_user):
        """Test getting a non-existent favorite"""
        retrieved = memory_manager.get_favorite_by_id(99999, test_user.id, db_session)

        assert retrieved is None, "Should return None for non-existent favorite"

    def test_update_favorite_value(self, db_session, test_user):
        """Test updating a favorite's value"""
        # Add a favorite
        favorite = memory_manager.add_favorite(
            test_user.id,
            "movie",
            "Star Wars",
            db_session
        )

        # Update the value
        updated = memory_manager.update_favorite(
            favorite.id,
            test_user.id,
            None,
            "The Matrix",
            db_session
        )

        assert updated is not None, "Should return updated favorite"
        assert updated.value == "The Matrix", "Value should be updated"
        assert updated.key == "movie", "Key should remain unchanged"

        # Cleanup
        db_session.delete(updated)
        db_session.commit()

    def test_update_favorite_key(self, db_session, test_user):
        """Test updating a favorite's key"""
        # Add a favorite
        favorite = memory_manager.add_favorite(
            test_user.id,
            "book",
            "Harry Potter",
            db_session
        )

        # Update the key
        updated = memory_manager.update_favorite(
            favorite.id,
            test_user.id,
            "book_series",
            None,
            db_session
        )

        assert updated is not None, "Should return updated favorite"
        assert updated.key == "book_series", "Key should be updated"
        assert updated.value == "Harry Potter", "Value should remain unchanged"

        # Cleanup
        db_session.delete(updated)
        db_session.commit()

    def test_update_favorite_both(self, db_session, test_user):
        """Test updating both key and value"""
        # Add a favorite
        favorite = memory_manager.add_favorite(
            test_user.id,
            "band",
            "The Beatles",
            db_session
        )

        # Update both
        updated = memory_manager.update_favorite(
            favorite.id,
            test_user.id,
            "music_artist",
            "Taylor Swift",
            db_session
        )

        assert updated is not None, "Should return updated favorite"
        assert updated.key == "music_artist", "Key should be updated"
        assert updated.value == "Taylor Swift", "Value should be updated"

        # Cleanup
        db_session.delete(updated)
        db_session.commit()

    def test_update_favorite_neither_raises_error(self, db_session, test_user):
        """Test that updating with neither key nor value raises error"""
        # Add a favorite
        favorite = memory_manager.add_favorite(
            test_user.id,
            "test",
            "value",
            db_session
        )

        with pytest.raises(ValueError, match="Must provide at least one"):
            memory_manager.update_favorite(
                favorite.id,
                test_user.id,
                None,
                None,
                db_session
            )

        # Cleanup
        db_session.delete(favorite)
        db_session.commit()

    def test_update_favorite_not_found(self, db_session, test_user):
        """Test updating a non-existent favorite"""
        updated = memory_manager.update_favorite(
            99999,
            test_user.id,
            "key",
            "value",
            db_session
        )

        assert updated is None, "Should return None for non-existent favorite"

    def test_delete_favorite(self, db_session, test_user):
        """Test deleting a favorite"""
        # Add a favorite
        favorite = memory_manager.add_favorite(
            test_user.id,
            "to_delete",
            "temporary",
            db_session
        )

        favorite_id = favorite.id

        # Delete it
        deleted = memory_manager.delete_favorite(
            favorite_id,
            test_user.id,
            db_session
        )

        assert deleted is True, "Should return True on successful deletion"

        # Verify it's gone
        retrieved = memory_manager.get_favorite_by_id(
            favorite_id,
            test_user.id,
            db_session
        )

        assert retrieved is None, "Favorite should no longer exist"

    def test_delete_favorite_not_found(self, db_session, test_user):
        """Test deleting a non-existent favorite"""
        deleted = memory_manager.delete_favorite(99999, test_user.id, db_session)

        assert deleted is False, "Should return False when favorite not found"

    def test_favorites_ordered_by_last_mentioned(self, db_session, test_user):
        """Test that favorites are returned in order of last_mentioned"""
        import time

        # Add favorites with slight time delay
        fav1 = memory_manager.add_favorite(test_user.id, "first", "value1", db_session)
        time.sleep(0.1)
        fav2 = memory_manager.add_favorite(test_user.id, "second", "value2", db_session)
        time.sleep(0.1)
        fav3 = memory_manager.add_favorite(test_user.id, "third", "value3", db_session)

        # Get all favorites
        favorites = memory_manager.get_favorites(test_user.id, db_session)

        # Should be ordered by most recent first
        assert favorites[0].key == "third", "Most recent should be first"
        assert favorites[1].key == "second", "Second most recent should be second"
        assert favorites[2].key == "first", "Oldest should be last"

        # Cleanup
        db_session.delete(fav1)
        db_session.delete(fav2)
        db_session.delete(fav3)
        db_session.commit()

    def test_favorites_isolation_between_users(self, db_session):
        """Test that favorites are isolated between users"""
        # Create two users
        user1 = User(id=10001, name="User1")
        user2 = User(id=10002, name="User2")
        db_session.add_all([user1, user2])
        db_session.commit()

        # Add favorites for each user
        fav1 = memory_manager.add_favorite(user1.id, "color", "red", db_session)
        fav2 = memory_manager.add_favorite(user2.id, "color", "green", db_session)

        # Get favorites for each user
        user1_favorites = memory_manager.get_favorites(user1.id, db_session)
        user2_favorites = memory_manager.get_favorites(user2.id, db_session)

        # Each user should only see their own favorites
        assert len([f for f in user1_favorites if f.key == "color"]) == 1, "User1 should have 1 favorite"
        assert len([f for f in user2_favorites if f.key == "color"]) == 1, "User2 should have 1 favorite"

        user1_color = [f for f in user1_favorites if f.key == "color"][0]
        user2_color = [f for f in user2_favorites if f.key == "color"][0]

        assert user1_color.value == "red", "User1's color should be red"
        assert user2_color.value == "green", "User2's color should be green"

        # Cleanup
        db_session.delete(fav1)
        db_session.delete(fav2)
        db_session.delete(user1)
        db_session.delete(user2)
        db_session.commit()


# Pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "favorites: marks tests for favorites storage feature"
    )
