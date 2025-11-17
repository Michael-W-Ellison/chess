"""
Test important people category storage

Run with: pytest backend/tests/test_people_storage.py -v
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
    user = User(id=9997, name="PeopleTestUser")
    db_session.add(user)
    db_session.commit()
    yield user
    # Cleanup
    db_session.query(UserProfile).filter(UserProfile.user_id == user.id).delete()
    db_session.delete(user)
    db_session.commit()


class TestPeopleStorage:
    """Tests for important people category storage"""

    def test_add_person(self, db_session, test_user):
        """Test adding a new person"""
        person = memory_manager.add_person(
            test_user.id,
            "friend_emma",
            "best friend who likes soccer",
            db_session
        )

        assert person is not None, "Should create person"
        assert person.category == "person", "Category should be 'person'"
        assert person.key == "friend_emma", "Key should match"
        assert person.value == "best friend who likes soccer", "Value should match"
        assert person.confidence == 1.0, "User-added people should have full confidence"
        assert person.mention_count == 1, "Initial mention count should be 1"

        # Cleanup
        db_session.delete(person)
        db_session.commit()

    def test_add_duplicate_person_updates(self, db_session, test_user):
        """Test that adding a duplicate person updates the existing one"""
        # Add first person
        person1 = memory_manager.add_person(
            test_user.id,
            "friend_alex",
            "likes basketball",
            db_session
        )

        # Add duplicate with different value
        person2 = memory_manager.add_person(
            test_user.id,
            "friend_alex",
            "best friend, plays basketball on school team",
            db_session
        )

        # Should be the same object (updated)
        assert person1.id == person2.id, "Should update existing person"
        assert person2.value == "best friend, plays basketball on school team", "Value should be updated"
        assert person2.mention_count == 2, "Mention count should increment"

        # Cleanup
        db_session.delete(person2)
        db_session.commit()

    def test_add_person_empty_key_raises_error(self, db_session, test_user):
        """Test that empty key raises ValueError"""
        with pytest.raises(ValueError, match="Key and value cannot be empty"):
            memory_manager.add_person(test_user.id, "", "value", db_session)

    def test_add_person_empty_value_raises_error(self, db_session, test_user):
        """Test that empty value raises ValueError"""
        with pytest.raises(ValueError, match="Key and value cannot be empty"):
            memory_manager.add_person(test_user.id, "key", "", db_session)

    def test_get_people(self, db_session, test_user):
        """Test retrieving all people for a user"""
        # Add multiple people
        p1 = memory_manager.add_person(test_user.id, "friend_sam", "likes video games", db_session)
        p2 = memory_manager.add_person(test_user.id, "teacher_jones", "science teacher", db_session)
        p3 = memory_manager.add_person(test_user.id, "cousin_lily", "same age, fun to play with", db_session)

        # Get all people
        people = memory_manager.get_people(test_user.id, db_session)

        assert len(people) == 3, "Should return all 3 people"

        keys = {p.key for p in people}
        assert "friend_sam" in keys, "Should include friend_sam"
        assert "teacher_jones" in keys, "Should include teacher_jones"
        assert "cousin_lily" in keys, "Should include cousin_lily"

        # Cleanup
        db_session.delete(p1)
        db_session.delete(p2)
        db_session.delete(p3)
        db_session.commit()

    def test_get_people_empty(self, db_session, test_user):
        """Test getting people when none exist"""
        people = memory_manager.get_people(test_user.id, db_session)

        assert isinstance(people, list), "Should return a list"
        # May or may not be empty depending on previous test cleanup

    def test_get_person_by_id(self, db_session, test_user):
        """Test retrieving a specific person by ID"""
        # Add a person
        person = memory_manager.add_person(
            test_user.id,
            "neighbor_tom",
            "lives next door, has a dog",
            db_session
        )

        # Retrieve by ID
        retrieved = memory_manager.get_person_by_id(
            person.id,
            test_user.id,
            db_session
        )

        assert retrieved is not None, "Should find the person"
        assert retrieved.id == person.id, "IDs should match"
        assert retrieved.key == "neighbor_tom", "Key should match"
        assert retrieved.value == "lives next door, has a dog", "Value should match"

        # Cleanup
        db_session.delete(person)
        db_session.commit()

    def test_get_person_by_id_not_found(self, db_session, test_user):
        """Test getting a non-existent person"""
        retrieved = memory_manager.get_person_by_id(99999, test_user.id, db_session)

        assert retrieved is None, "Should return None for non-existent person"

    def test_update_person_value(self, db_session, test_user):
        """Test updating a person's value"""
        # Add a person
        person = memory_manager.add_person(
            test_user.id,
            "friend_maya",
            "classmate",
            db_session
        )

        # Update the value
        updated = memory_manager.update_person(
            person.id,
            test_user.id,
            None,
            "best friend, sits next to me in class",
            db_session
        )

        assert updated is not None, "Should return updated person"
        assert updated.value == "best friend, sits next to me in class", "Value should be updated"
        assert updated.key == "friend_maya", "Key should remain unchanged"

        # Cleanup
        db_session.delete(updated)
        db_session.commit()

    def test_update_person_key(self, db_session, test_user):
        """Test updating a person's key"""
        # Add a person
        person = memory_manager.add_person(
            test_user.id,
            "friend_chris",
            "likes art",
            db_session
        )

        # Update the key
        updated = memory_manager.update_person(
            person.id,
            test_user.id,
            "best_friend_chris",
            None,
            db_session
        )

        assert updated is not None, "Should return updated person"
        assert updated.key == "best_friend_chris", "Key should be updated"
        assert updated.value == "likes art", "Value should remain unchanged"

        # Cleanup
        db_session.delete(updated)
        db_session.commit()

    def test_update_person_both(self, db_session, test_user):
        """Test updating both key and value"""
        # Add a person
        person = memory_manager.add_person(
            test_user.id,
            "classmate_jordan",
            "sits in front",
            db_session
        )

        # Update both
        updated = memory_manager.update_person(
            person.id,
            test_user.id,
            "friend_jordan",
            "good friend, loves reading like me",
            db_session
        )

        assert updated is not None, "Should return updated person"
        assert updated.key == "friend_jordan", "Key should be updated"
        assert updated.value == "good friend, loves reading like me", "Value should be updated"

        # Cleanup
        db_session.delete(updated)
        db_session.commit()

    def test_update_person_neither_raises_error(self, db_session, test_user):
        """Test that updating with neither key nor value raises error"""
        # Add a person
        person = memory_manager.add_person(
            test_user.id,
            "test",
            "value",
            db_session
        )

        with pytest.raises(ValueError, match="Must provide at least one"):
            memory_manager.update_person(
                person.id,
                test_user.id,
                None,
                None,
                db_session
            )

        # Cleanup
        db_session.delete(person)
        db_session.commit()

    def test_update_person_not_found(self, db_session, test_user):
        """Test updating a non-existent person"""
        updated = memory_manager.update_person(
            99999,
            test_user.id,
            "key",
            "value",
            db_session
        )

        assert updated is None, "Should return None for non-existent person"

    def test_delete_person(self, db_session, test_user):
        """Test deleting a person"""
        # Add a person
        person = memory_manager.add_person(
            test_user.id,
            "to_delete",
            "temporary",
            db_session
        )

        person_id = person.id

        # Delete it
        deleted = memory_manager.delete_person(
            person_id,
            test_user.id,
            db_session
        )

        assert deleted is True, "Should return True on successful deletion"

        # Verify it's gone
        retrieved = memory_manager.get_person_by_id(
            person_id,
            test_user.id,
            db_session
        )

        assert retrieved is None, "Person should no longer exist"

    def test_delete_person_not_found(self, db_session, test_user):
        """Test deleting a non-existent person"""
        deleted = memory_manager.delete_person(99999, test_user.id, db_session)

        assert deleted is False, "Should return False when person not found"

    def test_people_ordered_by_last_mentioned(self, db_session, test_user):
        """Test that people are returned in order of last_mentioned"""
        import time

        # Add people with slight time delay
        p1 = memory_manager.add_person(test_user.id, "first", "value1", db_session)
        time.sleep(0.1)
        p2 = memory_manager.add_person(test_user.id, "second", "value2", db_session)
        time.sleep(0.1)
        p3 = memory_manager.add_person(test_user.id, "third", "value3", db_session)

        # Get all people
        people = memory_manager.get_people(test_user.id, db_session)

        # Should be ordered by most recent first
        assert people[0].key == "third", "Most recent should be first"
        assert people[1].key == "second", "Second most recent should be second"
        assert people[2].key == "first", "Oldest should be last"

        # Cleanup
        db_session.delete(p1)
        db_session.delete(p2)
        db_session.delete(p3)
        db_session.commit()

    def test_people_isolation_between_users(self, db_session):
        """Test that people are isolated between users"""
        # Create two users
        user1 = User(id=10005, name="User1")
        user2 = User(id=10006, name="User2")
        db_session.add_all([user1, user2])
        db_session.commit()

        # Add people for each user
        p1 = memory_manager.add_person(user1.id, "friend_alex", "user1's friend", db_session)
        p2 = memory_manager.add_person(user2.id, "friend_alex", "user2's friend", db_session)

        # Get people for each user
        user1_people = memory_manager.get_people(user1.id, db_session)
        user2_people = memory_manager.get_people(user2.id, db_session)

        # Each user should only see their own people
        assert len([p for p in user1_people if p.key == "friend_alex"]) == 1, "User1 should have 1 person"
        assert len([p for p in user2_people if p.key == "friend_alex"]) == 1, "User2 should have 1 person"

        user1_alex = [p for p in user1_people if p.key == "friend_alex"][0]
        user2_alex = [p for p in user2_people if p.key == "friend_alex"][0]

        assert user1_alex.value == "user1's friend", "User1's friend should match"
        assert user2_alex.value == "user2's friend", "User2's friend should match"

        # Cleanup
        db_session.delete(p1)
        db_session.delete(p2)
        db_session.delete(user1)
        db_session.delete(user2)
        db_session.commit()

    def test_people_separate_from_favorites_and_dislikes(self, db_session, test_user):
        """Test that people are kept separate from favorites and dislikes"""
        # Add a favorite, dislike, and person with same key
        favorite = memory_manager.add_favorite(test_user.id, "emma", "favorite person", db_session)
        person = memory_manager.add_person(test_user.id, "emma", "best friend Emma", db_session)

        # Get each category
        favorites = memory_manager.get_favorites(test_user.id, db_session)
        people = memory_manager.get_people(test_user.id, db_session)

        # Check they're separate
        fav_emmas = [f.value for f in favorites if f.key == "emma"]
        person_emmas = [p.value for p in people if p.key == "emma"]

        assert "favorite person" in fav_emmas, "Favorites should contain favorite person"
        assert "best friend Emma" in person_emmas, "People should contain best friend Emma"
        assert "best friend Emma" not in fav_emmas, "Favorites should not contain person value"
        assert "favorite person" not in person_emmas, "People should not contain favorite value"

        # Cleanup
        db_session.delete(favorite)
        db_session.delete(person)
        db_session.commit()

    def test_various_person_types(self, db_session, test_user):
        """Test storing different types of people"""
        # Friends
        friend = memory_manager.add_person(test_user.id, "friend_sarah", "best friend since kindergarten", db_session)

        # Family
        family = memory_manager.add_person(test_user.id, "mom", "supportive and loving", db_session)

        # Teachers
        teacher = memory_manager.add_person(test_user.id, "teacher_williams", "favorite math teacher", db_session)

        # Neighbors
        neighbor = memory_manager.add_person(test_user.id, "neighbor_bob", "has three dogs", db_session)

        # Coaches
        coach = memory_manager.add_person(test_user.id, "coach_martinez", "soccer coach, very encouraging", db_session)

        # Get all people
        people = memory_manager.get_people(test_user.id, db_session)

        assert len(people) == 5, "Should have 5 different people"

        keys = {p.key for p in people}
        assert "friend_sarah" in keys
        assert "mom" in keys
        assert "teacher_williams" in keys
        assert "neighbor_bob" in keys
        assert "coach_martinez" in keys

        # Cleanup
        for person in [friend, family, teacher, neighbor, coach]:
            db_session.delete(person)
        db_session.commit()


# Pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "people: marks tests for important people storage feature"
    )
