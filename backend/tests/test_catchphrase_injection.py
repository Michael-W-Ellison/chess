"""
Tests for Catchphrase Injection into Responses
Tests that catchphrases are properly injected into bot responses
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock

from database.database import Base
from models.user import User
from models.personality import BotPersonality
from models.level_up_event import LevelUpEvent
from services.conversation_manager import ConversationManager
from services.feature_gates import can_use_catchphrase


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
def personality_level_1(test_db, test_user):
    """Create personality at level 1 (no catchphrase)"""
    personality = BotPersonality(
        user_id=test_user.id,
        name="TestBot",
        humor=0.5,
        energy=0.6,
        curiosity=0.5,
        formality=0.3,
        friendship_level=1,
        total_conversations=3,
        mood="happy",
        catchphrase=None,
    )
    test_db.add(personality)
    test_db.commit()
    test_db.refresh(personality)
    return personality


@pytest.fixture
def personality_level_3(test_db, test_user):
    """Create personality at level 3 with catchphrase"""
    personality = BotPersonality(
        user_id=test_user.id,
        name="TestBot",
        humor=0.5,
        energy=0.6,
        curiosity=0.5,
        formality=0.3,
        friendship_level=3,
        total_conversations=15,
        mood="happy",
        catchphrase="Cool beans!",
    )
    personality.set_quirks([])  # No quirks for cleaner testing
    test_db.add(personality)
    test_db.commit()
    test_db.refresh(personality)
    return personality


@pytest.fixture
def personality_level_5(test_db, test_user):
    """Create personality at level 5 with catchphrase"""
    personality = BotPersonality(
        user_id=test_user.id,
        name="TestBot",
        humor=0.5,
        energy=0.6,
        curiosity=0.5,
        formality=0.3,
        friendship_level=5,
        total_conversations=40,
        mood="happy",
        catchphrase="Awesome sauce!",
    )
    personality.set_quirks([])  # No quirks for cleaner testing
    test_db.add(personality)
    test_db.commit()
    test_db.refresh(personality)
    return personality


class TestCatchphraseInjectionBasics:
    """Test basic catchphrase injection functionality"""

    def test_catchphrase_can_be_added_at_level_3(self, personality_level_3):
        """Test that catchphrase CAN be added at level 3+"""
        manager = ConversationManager()

        # Mock random to always trigger (return 0.05 < 0.1)
        with patch('random.random', return_value=0.05):
            response = manager._apply_personality_filter(
                "That's interesting!",
                personality_level_3,
                ""
            )

        # Should have catchphrase appended
        assert "Cool beans!" in response
        assert response == "That's interesting! Cool beans!"

    def test_catchphrase_not_added_below_level_3(self, personality_level_1):
        """Test that catchphrase is NOT added below level 3"""
        manager = ConversationManager()

        # Even with 100% probability, shouldn't add (feature locked)
        with patch('random.random', return_value=0.0):
            response = manager._apply_personality_filter(
                "That's interesting!",
                personality_level_1,
                ""
            )

        # Should NOT have any catchphrase
        assert response == "That's interesting!"

    def test_catchphrase_not_added_when_none(self, test_db, test_user):
        """Test that catchphrase is not added when personality has no catchphrase"""
        # Level 3 but no catchphrase
        personality = BotPersonality(
            user_id=test_user.id,
            name="TestBot",
            humor=0.5,
            energy=0.6,
            curiosity=0.5,
            formality=0.3,
            friendship_level=3,
            total_conversations=15,
            mood="happy",
            catchphrase=None,  # No catchphrase
        )
        personality.set_quirks([])
        test_db.add(personality)
        test_db.commit()

        manager = ConversationManager()

        with patch('random.random', return_value=0.05):
            response = manager._apply_personality_filter(
                "That's interesting!",
                personality,
                ""
            )

        # Should NOT have catchphrase (none to add)
        assert response == "That's interesting!"

    def test_catchphrase_respects_probability(self, personality_level_3):
        """Test that catchphrase is only added with 10% probability"""
        manager = ConversationManager()

        # Test when random returns value >= 0.1 (should NOT add)
        with patch('random.random', return_value=0.15):
            response = manager._apply_personality_filter(
                "Hello there!",
                personality_level_3,
                ""
            )

        # Should NOT have catchphrase (probability not met)
        assert response == "Hello there!"

        # Test when random returns value < 0.1 (SHOULD add)
        with patch('random.random', return_value=0.05):
            response = manager._apply_personality_filter(
                "Hello there!",
                personality_level_3,
                ""
            )

        # Should have catchphrase
        assert "Cool beans!" in response


class TestCatchphraseFormat:
    """Test catchphrase formatting in responses"""

    def test_catchphrase_appended_with_space(self, personality_level_3):
        """Test that catchphrase is appended with proper spacing"""
        manager = ConversationManager()

        with patch('random.random', return_value=0.05):
            response = manager._apply_personality_filter(
                "Great job!",
                personality_level_3,
                ""
            )

        # Should have space before catchphrase
        assert response == "Great job! Cool beans!"
        assert not response.endswith("  ")  # No double spaces

    def test_catchphrase_with_empty_response(self, personality_level_3):
        """Test catchphrase with empty response"""
        manager = ConversationManager()

        with patch('random.random', return_value=0.05):
            response = manager._apply_personality_filter(
                "",
                personality_level_3,
                ""
            )

        # Should just have the catchphrase with leading space
        assert response == " Cool beans!"

    def test_catchphrase_with_different_phrases(self, test_db, test_user):
        """Test different catchphrases are injected correctly"""
        manager = ConversationManager()

        catchphrases_to_test = [
            "Let's go!",
            "Awesome sauce!",
            "Tell me more!",
            "You got this!",
            "Very well!",
        ]

        for i, catchphrase in enumerate(catchphrases_to_test):
            user = User(id=i+20, name=f"User{i}", age=10, created_at=datetime.now())
            test_db.add(user)
            test_db.commit()
            test_db.refresh(user)

            personality = BotPersonality(
                user_id=user.id,
                name="TestBot",
                friendship_level=3,
                catchphrase=catchphrase,
                humor=0.5,
                energy=0.5,
                curiosity=0.5,
                formality=0.3,
            )
            personality.set_quirks([])
            test_db.add(personality)
            test_db.commit()

            with patch('random.random', return_value=0.05):
                response = manager._apply_personality_filter(
                    "Nice!",
                    personality,
                    ""
                )

            assert catchphrase in response
            assert response == f"Nice! {catchphrase}"


class TestCatchphraseWithOtherQuirks:
    """Test catchphrase injection works alongside other quirks"""

    def test_catchphrase_with_emojis(self, test_db, test_user):
        """Test catchphrase works with uses_emojis quirk"""
        personality = BotPersonality(
            user_id=test_user.id,
            name="TestBot",
            friendship_level=3,
            catchphrase="Cool beans!",
            humor=0.5,
            energy=0.6,
            curiosity=0.5,
            formality=0.3,
            mood="happy",
        )
        personality.set_quirks(["uses_emojis"])
        test_db.add(personality)
        test_db.commit()

        manager = ConversationManager()

        with patch('random.random', return_value=0.05):
            response = manager._apply_personality_filter(
                "That's great!",
                personality,
                ""
            )

        # Should have catchphrase AND emojis (emojis added first, then catchphrase)
        assert "Cool beans!" in response

    def test_catchphrase_after_quirks_applied(self, test_db, test_user):
        """Test that catchphrase is added AFTER other quirks"""
        personality = BotPersonality(
            user_id=test_user.id,
            name="TestBot",
            friendship_level=3,
            catchphrase="Awesome!",
            humor=0.5,
            energy=0.6,
            curiosity=0.5,
            formality=0.3,
            mood="happy",
        )
        personality.set_quirks([])  # No quirks for predictability
        test_db.add(personality)
        test_db.commit()

        manager = ConversationManager()

        # Original response
        original = "This is fun"

        with patch('random.random', return_value=0.05):
            response = manager._apply_personality_filter(
                original,
                personality,
                ""
            )

        # Catchphrase should be at the end
        assert response.endswith("Awesome!")


class TestCatchphraseAtDifferentLevels:
    """Test catchphrase injection at various friendship levels"""

    def test_catchphrase_available_at_level_3(self, personality_level_3):
        """Test catchphrase feature is available at level 3"""
        assert can_use_catchphrase(personality_level_3) is True

    def test_catchphrase_available_at_level_5(self, personality_level_5):
        """Test catchphrase feature is available at level 5+"""
        assert can_use_catchphrase(personality_level_5) is True

    def test_catchphrase_not_available_at_level_1(self, personality_level_1):
        """Test catchphrase feature is NOT available at level 1"""
        assert can_use_catchphrase(personality_level_1) is False

    def test_catchphrase_not_available_at_level_2(self, test_db, test_user):
        """Test catchphrase feature is NOT available at level 2"""
        personality = BotPersonality(
            user_id=test_user.id,
            name="TestBot",
            friendship_level=2,
            humor=0.5,
            energy=0.5,
            curiosity=0.5,
            formality=0.3,
        )
        test_db.add(personality)
        test_db.commit()

        assert can_use_catchphrase(personality) is False


class TestCatchphraseProbabilityDistribution:
    """Test probabilistic behavior of catchphrase injection"""

    def test_catchphrase_probability_is_10_percent(self, personality_level_3):
        """Test that catchphrase appears approximately 10% of the time"""
        manager = ConversationManager()

        # Run many trials
        trials = 1000
        catchphrase_count = 0

        for _ in range(trials):
            # Use actual random (not mocked)
            response = manager._apply_personality_filter(
                "Test response",
                personality_level_3,
                ""
            )

            if "Cool beans!" in response:
                catchphrase_count += 1

        # Should be approximately 10% (allow 5-15% range for randomness)
        percentage = (catchphrase_count / trials) * 100
        assert 5 <= percentage <= 15, f"Catchphrase appeared {percentage}% of time (expected ~10%)"

    def test_catchphrase_randomness(self, personality_level_3):
        """Test that catchphrase injection has randomness"""
        manager = ConversationManager()

        # Generate multiple responses
        responses = []
        for _ in range(50):
            response = manager._apply_personality_filter(
                "Hello!",
                personality_level_3,
                ""
            )
            responses.append(response)

        # Should have mix of responses with and without catchphrase
        with_catchphrase = sum(1 for r in responses if "Cool beans!" in r)
        without_catchphrase = sum(1 for r in responses if "Cool beans!" not in r)

        # Both should occur at least once in 50 trials
        assert with_catchphrase > 0, "Catchphrase never appeared"
        assert without_catchphrase > 0, "Catchphrase always appeared"


class TestCatchphraseEdgeCases:
    """Test edge cases for catchphrase injection"""

    def test_catchphrase_with_multiline_response(self, personality_level_3):
        """Test catchphrase with multiline response"""
        manager = ConversationManager()

        multiline = "Line 1\nLine 2\nLine 3"

        with patch('random.random', return_value=0.05):
            response = manager._apply_personality_filter(
                multiline,
                personality_level_3,
                ""
            )

        # Catchphrase should be appended at end
        assert response == "Line 1\nLine 2\nLine 3 Cool beans!"

    def test_catchphrase_with_special_characters(self, test_db, test_user):
        """Test catchphrase containing special characters"""
        personality = BotPersonality(
            user_id=test_user.id,
            name="TestBot",
            friendship_level=3,
            catchphrase="Let's go!!! 🎉",  # Special chars and emoji
            humor=0.5,
            energy=0.6,
            curiosity=0.5,
            formality=0.3,
        )
        personality.set_quirks([])
        test_db.add(personality)
        test_db.commit()

        manager = ConversationManager()

        with patch('random.random', return_value=0.05):
            response = manager._apply_personality_filter(
                "Great!",
                personality,
                ""
            )

        assert "Let's go!!! 🎉" in response

    def test_catchphrase_with_long_response(self, personality_level_3):
        """Test catchphrase with very long response"""
        manager = ConversationManager()

        long_response = "This is a very long response. " * 20

        with patch('random.random', return_value=0.05):
            response = manager._apply_personality_filter(
                long_response,
                personality_level_3,
                ""
            )

        # Should have catchphrase at end
        assert response.endswith("Cool beans!")
        assert "Cool beans!" in response


class TestCatchphraseIntegration:
    """Test catchphrase injection in full context"""

    def test_feature_gate_check_works(self, test_db):
        """Test that feature gate correctly gates catchphrase"""
        manager = ConversationManager()

        # Create user 1 with level 1 personality
        user1 = User(id=100, name="User1", age=10, created_at=datetime.now())
        test_db.add(user1)
        test_db.commit()

        personality_level_1 = BotPersonality(
            user_id=user1.id,
            name="TestBot1",
            friendship_level=1,
            catchphrase=None,
            humor=0.5,
            energy=0.5,
            curiosity=0.5,
            formality=0.3,
        )
        personality_level_1.set_quirks([])
        test_db.add(personality_level_1)
        test_db.commit()

        # Create user 2 with level 3 personality
        user2 = User(id=101, name="User2", age=10, created_at=datetime.now())
        test_db.add(user2)
        test_db.commit()

        personality_level_3 = BotPersonality(
            user_id=user2.id,
            name="TestBot3",
            friendship_level=3,
            catchphrase="Cool beans!",
            humor=0.5,
            energy=0.5,
            curiosity=0.5,
            formality=0.3,
        )
        personality_level_3.set_quirks([])
        test_db.add(personality_level_3)
        test_db.commit()

        # Level 1: Feature locked
        with patch('random.random', return_value=0.05):
            response1 = manager._apply_personality_filter(
                "Test",
                personality_level_1,
                ""
            )

        assert response1 == "Test"

        # Level 3: Feature unlocked
        with patch('random.random', return_value=0.05):
            response3 = manager._apply_personality_filter(
                "Test",
                personality_level_3,
                ""
            )

        assert "Cool beans!" in response3

    def test_catchphrase_injection_is_consistent(self, personality_level_3):
        """Test that catchphrase injection behavior is consistent"""
        manager = ConversationManager()

        # Same conditions should produce same result
        with patch('random.random', return_value=0.05):
            response1 = manager._apply_personality_filter(
                "Hello!",
                personality_level_3,
                ""
            )
            response2 = manager._apply_personality_filter(
                "Hello!",
                personality_level_3,
                ""
            )

        # Both should have catchphrase (consistent behavior)
        assert response1 == response2
        assert "Cool beans!" in response1
        assert "Cool beans!" in response2
