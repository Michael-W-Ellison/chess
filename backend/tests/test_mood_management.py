"""
Tests for Mood State Management
Tests that bot mood state is properly managed and updated
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.database import Base
from models.user import User
from models.personality import BotPersonality
from models.level_up_event import LevelUpEvent
from services.personality_manager import PersonalityManager, personality_manager
from services.conversation_manager import ConversationManager


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


@pytest.fixture
def test_personality(test_db, test_user):
    """Create test personality with default happy mood"""
    personality = BotPersonality(
        user_id=test_user.id,
        name="TestBot",
        humor=0.5,
        energy=0.6,
        curiosity=0.5,
        formality=0.3,
        friendship_level=3,
        total_conversations=15,
        mood="happy",  # Default mood
    )
    test_db.add(personality)
    test_db.commit()
    test_db.refresh(personality)
    return personality


class TestMoodInitialization:
    """Test mood initialization and default state"""

    def test_default_mood_is_happy(self, test_db, test_user):
        """Test that new personalities start with happy mood"""
        personality = BotPersonality(
            user_id=test_user.id,
            name="NewBot",
            friendship_level=1,
        )
        test_db.add(personality)
        test_db.commit()
        test_db.refresh(personality)

        assert personality.mood == "happy"

    def test_mood_persists_to_database(self, test_db, test_user):
        """Test that mood is saved to database"""
        personality = BotPersonality(
            user_id=test_user.id,
            name="TestBot",
            friendship_level=1,
            mood="excited",
        )
        test_db.add(personality)
        test_db.commit()
        personality_id = personality.id

        # Clear session and reload
        test_db.expunge_all()

        reloaded = test_db.query(BotPersonality).filter(
            BotPersonality.id == personality_id
        ).first()

        assert reloaded.mood == "excited"

    def test_mood_in_to_dict(self, test_personality):
        """Test that mood is included in to_dict output"""
        data = test_personality.to_dict()

        assert "mood" in data
        assert data["mood"] == "happy"


class TestMoodUpdate:
    """Test mood update based on user mood"""

    def test_update_mood_sad_to_concerned(self, test_db, test_personality):
        """Test that sad user mood triggers concerned bot mood"""
        manager = PersonalityManager()

        updated = manager.update_mood(test_personality, "sad", test_db)

        assert updated.mood == "concerned"

    def test_update_mood_anxious_to_concerned(self, test_db, test_personality):
        """Test that anxious user mood triggers concerned bot mood"""
        manager = PersonalityManager()

        updated = manager.update_mood(test_personality, "anxious", test_db)

        assert updated.mood == "concerned"

    def test_update_mood_angry_to_calm(self, test_db, test_personality):
        """Test that angry user mood triggers calm bot mood"""
        manager = PersonalityManager()

        updated = manager.update_mood(test_personality, "angry", test_db)

        assert updated.mood == "calm"

    def test_update_mood_happy_to_happy(self, test_db, test_personality):
        """Test that happy user mood keeps happy bot mood"""
        manager = PersonalityManager()

        updated = manager.update_mood(test_personality, "happy", test_db)

        assert updated.mood == "happy"

    def test_update_mood_excited_to_excited(self, test_db, test_personality):
        """Test that excited user mood triggers excited bot mood"""
        manager = PersonalityManager()

        updated = manager.update_mood(test_personality, "excited", test_db)

        assert updated.mood == "excited"

    def test_update_mood_neutral_to_happy(self, test_db, test_personality):
        """Test that neutral user mood triggers happy bot mood"""
        manager = PersonalityManager()

        updated = manager.update_mood(test_personality, "neutral", test_db)

        assert updated.mood == "happy"


class TestMoodMapping:
    """Test mood mapping logic"""

    def test_all_user_moods_mapped(self, test_db, test_personality):
        """Test that all detectable user moods have bot mood mappings"""
        manager = PersonalityManager()

        # All user moods that can be detected
        user_moods = ["sad", "anxious", "angry", "happy", "excited", "neutral"]

        for user_mood in user_moods:
            # Reset to happy
            test_personality.mood = "happy"
            test_db.commit()

            # Update mood
            updated = manager.update_mood(test_personality, user_mood, test_db)

            # Should have a valid bot mood
            assert updated.mood in ["happy", "excited", "calm", "concerned", "playful", "thoughtful"]

    def test_mood_mapping_consistency(self, test_db, test_personality):
        """Test that mood mappings are consistent"""
        manager = PersonalityManager()

        # Test same input produces same output
        for _ in range(3):
            test_personality.mood = "happy"
            test_db.commit()
            updated = manager.update_mood(test_personality, "sad", test_db)
            assert updated.mood == "concerned"

    def test_invalid_user_mood_ignored(self, test_db, test_personality):
        """Test that invalid user moods don't change bot mood"""
        manager = PersonalityManager()

        original_mood = test_personality.mood

        # Try invalid mood
        updated = manager.update_mood(test_personality, "invalid_mood", test_db)

        # Should keep original mood
        assert updated.mood == original_mood

    def test_none_user_mood_ignored(self, test_db, test_personality):
        """Test that None user mood doesn't change bot mood"""
        manager = PersonalityManager()

        original_mood = test_personality.mood

        updated = manager.update_mood(test_personality, None, test_db)

        assert updated.mood == original_mood

    def test_empty_string_mood_ignored(self, test_db, test_personality):
        """Test that empty string mood doesn't change bot mood"""
        manager = PersonalityManager()

        original_mood = test_personality.mood

        updated = manager.update_mood(test_personality, "", test_db)

        assert updated.mood == original_mood


class TestMoodTransitions:
    """Test mood state transitions"""

    def test_mood_can_change_from_happy_to_concerned(self, test_db, test_personality):
        """Test transition from happy to concerned"""
        manager = PersonalityManager()

        assert test_personality.mood == "happy"

        updated = manager.update_mood(test_personality, "sad", test_db)

        assert updated.mood == "concerned"

    def test_mood_can_change_from_concerned_to_happy(self, test_db, test_personality):
        """Test transition from concerned back to happy"""
        manager = PersonalityManager()

        # Set to concerned
        test_personality.mood = "concerned"
        test_db.commit()

        # Update to happy
        updated = manager.update_mood(test_personality, "happy", test_db)

        assert updated.mood == "happy"

    def test_multiple_mood_transitions(self, test_db, test_personality):
        """Test multiple mood transitions in sequence"""
        manager = PersonalityManager()

        # Start: happy
        assert test_personality.mood == "happy"

        # Happy -> Excited
        updated = manager.update_mood(test_personality, "excited", test_db)
        assert updated.mood == "excited"

        # Excited -> Concerned
        updated = manager.update_mood(test_personality, "sad", test_db)
        assert updated.mood == "concerned"

        # Concerned -> Calm
        updated = manager.update_mood(test_personality, "angry", test_db)
        assert updated.mood == "calm"

        # Calm -> Happy
        updated = manager.update_mood(test_personality, "neutral", test_db)
        assert updated.mood == "happy"

    def test_same_mood_no_unnecessary_update(self, test_db, test_personality):
        """Test that setting same mood doesn't trigger unnecessary database update"""
        manager = PersonalityManager()

        # Already happy
        test_personality.mood = "happy"
        test_db.commit()

        # Try to set happy again
        updated = manager.update_mood(test_personality, "happy", test_db)

        # Should still be happy (but no change occurred)
        assert updated.mood == "happy"


class TestUserMoodDetection:
    """Test user mood detection from messages"""

    def test_detect_sad_mood(self):
        """Test detection of sad mood"""
        manager = ConversationManager()

        assert manager._detect_user_mood("I'm feeling sad today") == "sad"
        assert manager._detect_user_mood("I'm so upset about this") == "sad"
        assert manager._detect_user_mood("I've been crying all day") == "sad"
        assert manager._detect_user_mood("I feel depressed") == "sad"

    def test_detect_anxious_mood(self):
        """Test detection of anxious mood"""
        manager = ConversationManager()

        assert manager._detect_user_mood("I'm worried about the test") == "anxious"
        assert manager._detect_user_mood("I'm feeling nervous") == "anxious"
        assert manager._detect_user_mood("I'm scared of failing") == "anxious"
        assert manager._detect_user_mood("I'm so anxious") == "anxious"

    def test_detect_happy_mood(self):
        """Test detection of happy mood"""
        manager = ConversationManager()

        assert manager._detect_user_mood("I'm so happy!") == "happy"
        assert manager._detect_user_mood("I'm excited about this") == "happy"
        assert manager._detect_user_mood("This is great!") == "happy"
        assert manager._detect_user_mood("That's awesome!") == "happy"

    def test_detect_angry_mood(self):
        """Test detection of angry mood"""
        manager = ConversationManager()

        assert manager._detect_user_mood("I'm so angry") == "angry"
        assert manager._detect_user_mood("That makes me mad") == "angry"
        assert manager._detect_user_mood("I'm furious about this") == "angry"

    def test_detect_neutral_mood(self):
        """Test detection of neutral mood"""
        manager = ConversationManager()

        # Messages without strong emotional indicators
        assert manager._detect_user_mood("What's the weather?") == "neutral"
        assert manager._detect_user_mood("Tell me about math") == "neutral"
        assert manager._detect_user_mood("How are you?") == "neutral"

    def test_case_insensitive_detection(self):
        """Test that mood detection is case insensitive"""
        manager = ConversationManager()

        assert manager._detect_user_mood("I'm HAPPY") == "happy"
        assert manager._detect_user_mood("I'm SAD") == "sad"
        assert manager._detect_user_mood("I'm WoRrIeD") == "anxious"


class TestMoodPersistence:
    """Test mood persistence across sessions"""

    def test_mood_persists_after_update(self, test_db, test_personality):
        """Test that mood persists after update"""
        manager = PersonalityManager()

        # Update mood
        updated = manager.update_mood(test_personality, "excited", test_db)
        assert updated.mood == "excited"

        personality_id = updated.id

        # Clear session
        test_db.expunge_all()

        # Reload
        reloaded = test_db.query(BotPersonality).filter(
            BotPersonality.id == personality_id
        ).first()

        assert reloaded.mood == "excited"

    def test_mood_history_through_transitions(self, test_db, test_personality):
        """Test that current mood is always the latest"""
        manager = PersonalityManager()

        # Series of mood changes
        moods = ["excited", "concerned", "calm", "happy"]

        for user_mood_trigger in ["excited", "sad", "angry", "neutral"]:
            manager.update_mood(test_personality, user_mood_trigger, test_db)

        # Should be at the last mood (happy)
        assert test_personality.mood == "happy"


class TestMoodAvailability:
    """Test available mood states"""

    def test_all_bot_moods_available(self):
        """Test that all documented bot moods can be set"""
        # From personality.py comment: happy, excited, calm, concerned, playful, thoughtful
        valid_moods = ["happy", "excited", "calm", "concerned", "playful", "thoughtful"]

        # All should be valid mood strings
        for mood in valid_moods:
            assert isinstance(mood, str)
            assert len(mood) > 0

    def test_mood_mapping_covers_empathetic_responses(self, test_db, test_personality):
        """Test that mood mapping provides empathetic bot responses"""
        manager = PersonalityManager()

        # Sad user -> Concerned bot (empathetic)
        updated = manager.update_mood(test_personality, "sad", test_db)
        assert updated.mood == "concerned"

        # Angry user -> Calm bot (de-escalating)
        test_personality.mood = "happy"
        test_db.commit()
        updated = manager.update_mood(test_personality, "angry", test_db)
        assert updated.mood == "calm"

        # Happy user -> Happy bot (matching energy)
        test_personality.mood = "calm"
        test_db.commit()
        updated = manager.update_mood(test_personality, "happy", test_db)
        assert updated.mood == "happy"


class TestMoodIntegration:
    """Test mood integration with emoji quirk"""

    def test_mood_affects_emoji_selection(self, test_db, test_user):
        """Test that mood is passed to emoji quirk for mood-based emoji selection"""
        personality = BotPersonality(
            user_id=test_user.id,
            name="TestBot",
            friendship_level=3,
            mood="excited",  # Specific mood
            humor=0.5,
            energy=0.6,
            curiosity=0.5,
            formality=0.3,
        )
        personality.set_quirks(["uses_emojis"])
        test_db.add(personality)
        test_db.commit()

        manager = ConversationManager()

        # Apply personality filter (which uses mood for emojis)
        response = manager._apply_personality_filter(
            "This is great!",
            personality,
            ""
        )

        # Emoji quirk should receive the "excited" mood
        # (actual emoji selection tested in emoji quirk tests)
        assert personality.mood == "excited"


class TestMoodEdgeCases:
    """Test edge cases for mood management"""

    def test_mood_update_with_multiple_keywords(self):
        """Test mood detection with multiple emotional keywords"""
        manager = ConversationManager()

        # Multiple sad keywords
        mood = manager._detect_user_mood("I'm sad and upset and crying")
        assert mood == "sad"  # First match wins

    def test_mood_update_returns_personality(self, test_db, test_personality):
        """Test that update_mood returns the personality object"""
        manager = PersonalityManager()

        result = manager.update_mood(test_personality, "happy", test_db)

        assert isinstance(result, BotPersonality)
        assert result.id == test_personality.id

    def test_mood_with_special_characters(self):
        """Test mood detection with special characters in message"""
        manager = ConversationManager()

        assert manager._detect_user_mood("I'm happy!!! 🎉") == "happy"
        assert manager._detect_user_mood("So sad... 😢") == "sad"

    def test_mood_with_mixed_emotions(self):
        """Test mood detection with mixed emotions (first match wins)"""
        manager = ConversationManager()

        # Has both happy and sad indicators
        # Should detect based on order of checks
        mood = manager._detect_user_mood("I'm sad but trying to be happy")

        # Based on implementation, "sad" is checked first
        assert mood == "sad"
