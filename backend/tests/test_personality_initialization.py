"""
Tests for Personality Initialization
Tests quirk random assignment and initial personality setup
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.database import Base
from models.user import User
from models.personality import BotPersonality
from models.level_up_event import LevelUpEvent  # Import to resolve SQLAlchemy relationship
from services.personality_manager import PersonalityManager, personality_manager


@pytest.fixture
def test_db():
    """Create test database"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture
def test_user(test_db):
    """Create test user"""
    user = User(id=1, name="Test User", age=10, created_at=datetime.now())
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


class TestPersonalityInitialization:
    """Test personality initialization and quirk assignment"""

    def test_initialize_personality_creates_new_personality(self, test_db, test_user):
        """Test that initialize_personality creates a new personality"""
        manager = PersonalityManager()

        personality = manager.initialize_personality(test_user.id, test_db)

        assert personality is not None
        assert personality.user_id == test_user.id
        assert personality.name == "Buddy"  # Default name
        assert personality.friendship_level == 1
        assert personality.total_conversations == 0
        assert personality.mood == "happy"

    def test_initialize_personality_with_custom_name(self, test_db, test_user):
        """Test personality initialization with custom bot name"""
        manager = PersonalityManager()

        personality = manager.initialize_personality(
            test_user.id, test_db, bot_name="CustomBot"
        )

        assert personality.name == "CustomBot"

    def test_initialize_personality_assigns_random_quirks(self, test_db, test_user):
        """Test that personality gets 1-2 random quirks assigned"""
        manager = PersonalityManager()

        personality = manager.initialize_personality(test_user.id, test_db)

        quirks = personality.get_quirks()

        # Should have 1-2 quirks
        assert len(quirks) >= 1
        assert len(quirks) <= 2

        # All quirks should be from available quirks
        for quirk in quirks:
            assert quirk in manager.available_quirks

    def test_quirks_are_from_available_list(self, test_db, test_user):
        """Test that assigned quirks are from the available quirks list"""
        manager = PersonalityManager()

        personality = manager.initialize_personality(test_user.id, test_db)
        quirks = personality.get_quirks()

        # Available quirks should include the implemented ones
        available = manager.available_quirks
        assert "uses_emojis" in available
        assert "tells_puns" in available
        assert "shares_facts" in available

        # All assigned quirks must be from available list
        for quirk in quirks:
            assert quirk in available

    def test_quirks_are_unique(self, test_db, test_user):
        """Test that assigned quirks don't include duplicates"""
        manager = PersonalityManager()

        personality = manager.initialize_personality(test_user.id, test_db)
        quirks = personality.get_quirks()

        # No duplicates
        assert len(quirks) == len(set(quirks))

    def test_initialize_personality_assigns_interests(self, test_db, test_user):
        """Test that personality gets 2-3 random interests assigned"""
        manager = PersonalityManager()

        personality = manager.initialize_personality(test_user.id, test_db)

        interests = personality.get_interests()

        # Should have 2-3 interests
        assert len(interests) >= 2
        assert len(interests) <= 3

        # All interests should be from available interests
        for interest in interests:
            assert interest in manager.available_interests

    def test_interests_are_unique(self, test_db, test_user):
        """Test that assigned interests don't include duplicates"""
        manager = PersonalityManager()

        personality = manager.initialize_personality(test_user.id, test_db)
        interests = personality.get_interests()

        # No duplicates
        assert len(interests) == len(set(interests))

    def test_initialize_personality_sets_random_traits(self, test_db, test_user):
        """Test that personality traits are randomized within ranges"""
        manager = PersonalityManager()

        personality = manager.initialize_personality(test_user.id, test_db)

        # Humor: 0.3 to 0.8
        assert 0.3 <= personality.humor <= 0.8

        # Energy: 0.4 to 0.9
        assert 0.4 <= personality.energy <= 0.9

        # Curiosity: 0.3 to 0.8
        assert 0.3 <= personality.curiosity <= 0.8

        # Formality: 0.2 to 0.6
        assert 0.2 <= personality.formality <= 0.6

    def test_traits_vary_between_personalities(self, test_db):
        """Test that multiple personalities get different random traits"""
        manager = PersonalityManager()

        # Create multiple users and personalities
        personalities = []
        for i in range(5):
            user = User(id=i+10, name=f"User{i}", age=10, created_at=datetime.now())
            test_db.add(user)
            test_db.commit()
            test_db.refresh(user)

            personality = manager.initialize_personality(user.id, test_db)
            personalities.append(personality)

        # Check that not all have identical traits (very unlikely)
        humor_values = [p.humor for p in personalities]
        energy_values = [p.energy for p in personalities]

        # At least some variation should exist
        assert len(set(humor_values)) > 1 or len(set(energy_values)) > 1

    def test_quirks_vary_between_personalities(self, test_db):
        """Test that multiple personalities can get different quirk combinations"""
        manager = PersonalityManager()

        # Create multiple users and personalities
        quirk_sets = []
        for i in range(10):
            user = User(id=i+20, name=f"User{i}", age=10, created_at=datetime.now())
            test_db.add(user)
            test_db.commit()
            test_db.refresh(user)

            personality = manager.initialize_personality(user.id, test_db)
            quirks = tuple(sorted(personality.get_quirks()))  # Make hashable
            quirk_sets.append(quirks)

        # At least some variation should exist in quirk assignments
        unique_combinations = len(set(quirk_sets))
        assert unique_combinations > 1, "All personalities got identical quirks"

    def test_initialize_personality_prevents_duplicates(self, test_db, test_user):
        """Test that initialize_personality doesn't create duplicate personalities"""
        manager = PersonalityManager()

        # Create first personality
        personality1 = manager.initialize_personality(test_user.id, test_db)

        # Try to create second personality for same user
        personality2 = manager.initialize_personality(test_user.id, test_db)

        # Should return the same personality
        assert personality1.id == personality2.id

    def test_quirks_persist_to_database(self, test_db, test_user):
        """Test that quirks are properly persisted to database"""
        manager = PersonalityManager()

        personality = manager.initialize_personality(test_user.id, test_db)
        quirks_original = personality.get_quirks()
        personality_id = personality.id

        # Clear session and reload from database
        test_db.expunge_all()

        # Reload personality from database
        reloaded = test_db.query(BotPersonality).filter(
            BotPersonality.id == personality_id
        ).first()

        quirks_reloaded = reloaded.get_quirks()

        # Should have same quirks
        assert sorted(quirks_original) == sorted(quirks_reloaded)

    def test_interests_persist_to_database(self, test_db, test_user):
        """Test that interests are properly persisted to database"""
        manager = PersonalityManager()

        personality = manager.initialize_personality(test_user.id, test_db)
        interests_original = personality.get_interests()
        personality_id = personality.id

        # Clear session and reload from database
        test_db.expunge_all()

        # Reload personality from database
        reloaded = test_db.query(BotPersonality).filter(
            BotPersonality.id == personality_id
        ).first()

        interests_reloaded = reloaded.get_interests()

        # Should have same interests
        assert sorted(interests_original) == sorted(interests_reloaded)

    def test_global_personality_manager_instance(self, test_db, test_user):
        """Test that global personality_manager instance works"""
        personality = personality_manager.initialize_personality(test_user.id, test_db)

        assert personality is not None
        assert len(personality.get_quirks()) >= 1
        assert len(personality.get_interests()) >= 2


class TestQuirkAssignmentEdgeCases:
    """Test edge cases for quirk assignment"""

    def test_available_quirks_list_not_empty(self):
        """Test that available quirks list contains items"""
        manager = PersonalityManager()

        assert len(manager.available_quirks) > 0

        # Should have at least the implemented quirks
        assert "uses_emojis" in manager.available_quirks
        assert "tells_puns" in manager.available_quirks
        assert "shares_facts" in manager.available_quirks

    def test_available_interests_list_not_empty(self):
        """Test that available interests list contains items"""
        manager = PersonalityManager()

        assert len(manager.available_interests) > 0

        # Should have diverse interests
        assert len(manager.available_interests) >= 5

    def test_quirk_assignment_handles_all_available_quirks(self, test_db):
        """Test that over many initializations, all quirks can be assigned"""
        manager = PersonalityManager()

        # Track which quirks appear
        quirks_seen = set()

        # Create many personalities
        for i in range(50):
            user = User(id=i+100, name=f"User{i}", age=10, created_at=datetime.now())
            test_db.add(user)
            test_db.commit()
            test_db.refresh(user)

            personality = manager.initialize_personality(user.id, test_db)
            quirks_seen.update(personality.get_quirks())

        # Over 50 trials, we should see most/all available quirks
        # (Though not guaranteed due to randomness)
        assert len(quirks_seen) >= 2, "Too few quirks seen in random assignment"


class TestQuirkSetterGetter:
    """Test quirk setter/getter methods"""

    def test_set_and_get_quirks(self, test_db, test_user):
        """Test setting and getting quirks"""
        personality = BotPersonality(
            user_id=test_user.id,
            name="TestBot",
            friendship_level=1,
        )
        test_db.add(personality)
        test_db.commit()

        # Set quirks
        quirks = ["uses_emojis", "tells_puns"]
        personality.set_quirks(quirks)
        test_db.commit()

        # Get quirks
        retrieved = personality.get_quirks()
        assert sorted(retrieved) == sorted(quirks)

    def test_get_quirks_empty_returns_empty_list(self, test_db, test_user):
        """Test that get_quirks returns empty list when no quirks set"""
        personality = BotPersonality(
            user_id=test_user.id,
            name="TestBot",
            friendship_level=1,
        )
        test_db.add(personality)
        test_db.commit()

        quirks = personality.get_quirks()
        assert quirks == []

    def test_set_quirks_overwrites_previous(self, test_db, test_user):
        """Test that set_quirks overwrites previous quirks"""
        personality = BotPersonality(
            user_id=test_user.id,
            name="TestBot",
            friendship_level=1,
        )
        test_db.add(personality)
        test_db.commit()

        # Set initial quirks
        personality.set_quirks(["uses_emojis"])
        test_db.commit()

        # Overwrite with new quirks
        personality.set_quirks(["tells_puns", "shares_facts"])
        test_db.commit()

        # Should have new quirks only
        quirks = personality.get_quirks()
        assert sorted(quirks) == sorted(["tells_puns", "shares_facts"])
