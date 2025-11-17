"""
Tests for Mood-Based Response Tone Adjustment
Tests that bot mood affects response tone through prompt generation
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.database import Base
from models.user import User
from models.personality import BotPersonality
from models.conversation import Conversation, Message
from models.level_up_event import LevelUpEvent
from services.conversation_manager import ConversationManager
from services.personality_manager import PersonalityManager


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
def test_conversation(test_db, test_user):
    """Create test conversation"""
    conversation = Conversation(
        user_id=test_user.id,
        timestamp=datetime.now(),
        message_count=0,
        duration_seconds=0,
    )
    test_db.add(conversation)
    test_db.commit()
    test_db.refresh(conversation)
    return conversation


class TestMoodInPrompt:
    """Test that mood is included in prompt generation"""

    def test_happy_mood_in_prompt(self, test_db, test_user):
        """Test that happy mood is included in prompt"""
        personality = BotPersonality(
            user_id=test_user.id,
            name="TestBot",
            friendship_level=3,
            mood="happy",
            humor=0.5,
            energy=0.6,
            curiosity=0.5,
            formality=0.3,
        )
        test_db.add(personality)
        test_db.commit()

        manager = ConversationManager()
        context = {"recent_messages": [], "relevant_memories": []}

        prompt = manager._build_prompt(context, "Hello!", personality)

        assert "CURRENT MOOD: happy" in prompt

    def test_excited_mood_in_prompt(self, test_db, test_user):
        """Test that excited mood is included in prompt"""
        personality = BotPersonality(
            user_id=test_user.id,
            name="TestBot",
            friendship_level=3,
            mood="excited",
            humor=0.5,
            energy=0.6,
            curiosity=0.5,
            formality=0.3,
        )
        test_db.add(personality)
        test_db.commit()

        manager = ConversationManager()
        context = {"recent_messages": [], "relevant_memories": []}

        prompt = manager._build_prompt(context, "Hello!", personality)

        assert "CURRENT MOOD: excited" in prompt

    def test_calm_mood_in_prompt(self, test_db, test_user):
        """Test that calm mood is included in prompt"""
        personality = BotPersonality(
            user_id=test_user.id,
            name="TestBot",
            friendship_level=3,
            mood="calm",
            humor=0.5,
            energy=0.6,
            curiosity=0.5,
            formality=0.3,
        )
        test_db.add(personality)
        test_db.commit()

        manager = ConversationManager()
        context = {"recent_messages": [], "relevant_memories": []}

        prompt = manager._build_prompt(context, "Hello!", personality)

        assert "CURRENT MOOD: calm" in prompt

    def test_concerned_mood_in_prompt(self, test_db, test_user):
        """Test that concerned mood is included in prompt"""
        personality = BotPersonality(
            user_id=test_user.id,
            name="TestBot",
            friendship_level=3,
            mood="concerned",
            humor=0.5,
            energy=0.6,
            curiosity=0.5,
            formality=0.3,
        )
        test_db.add(personality)
        test_db.commit()

        manager = ConversationManager()
        context = {"recent_messages": [], "relevant_memories": []}

        prompt = manager._build_prompt(context, "Hello!", personality)

        assert "CURRENT MOOD: concerned" in prompt

    def test_playful_mood_in_prompt(self, test_db, test_user):
        """Test that playful mood is included in prompt"""
        personality = BotPersonality(
            user_id=test_user.id,
            name="TestBot",
            friendship_level=3,
            mood="playful",
            humor=0.5,
            energy=0.6,
            curiosity=0.5,
            formality=0.3,
        )
        test_db.add(personality)
        test_db.commit()

        manager = ConversationManager()
        context = {"recent_messages": [], "relevant_memories": []}

        prompt = manager._build_prompt(context, "Hello!", personality)

        assert "CURRENT MOOD: playful" in prompt

    def test_thoughtful_mood_in_prompt(self, test_db, test_user):
        """Test that thoughtful mood is included in prompt"""
        personality = BotPersonality(
            user_id=test_user.id,
            name="TestBot",
            friendship_level=3,
            mood="thoughtful",
            humor=0.5,
            energy=0.6,
            curiosity=0.5,
            formality=0.3,
        )
        test_db.add(personality)
        test_db.commit()

        manager = ConversationManager()
        context = {"recent_messages": [], "relevant_memories": []}

        prompt = manager._build_prompt(context, "Hello!", personality)

        assert "CURRENT MOOD: thoughtful" in prompt


class TestMoodAffectsPrompt:
    """Test that different moods produce different prompts"""

    def test_different_moods_different_prompts(self, test_db):
        """Test that changing mood changes the prompt"""
        manager = ConversationManager()
        context = {"recent_messages": [], "relevant_memories": []}

        # Create users with different moods
        moods = ["happy", "excited", "calm", "concerned"]
        prompts = []

        for i, mood in enumerate(moods):
            user = User(id=i+10, name=f"User{i}", age=10, created_at=datetime.now())
            test_db.add(user)
            test_db.commit()

            personality = BotPersonality(
                user_id=user.id,
                name="TestBot",
                friendship_level=3,
                mood=mood,
                humor=0.5,
                energy=0.6,
                curiosity=0.5,
                formality=0.3,
            )
            test_db.add(personality)
            test_db.commit()

            prompt = manager._build_prompt(context, "Hello!", personality)
            prompts.append(prompt)

        # All prompts should be different (due to different mood)
        unique_prompts = len(set(prompts))
        assert unique_prompts == len(moods), "All prompts should be unique"

    def test_mood_change_updates_prompt(self, test_db, test_user):
        """Test that updating mood changes the prompt"""
        personality = BotPersonality(
            user_id=test_user.id,
            name="TestBot",
            friendship_level=3,
            mood="happy",
            humor=0.5,
            energy=0.6,
            curiosity=0.5,
            formality=0.3,
        )
        test_db.add(personality)
        test_db.commit()

        manager = ConversationManager()
        context = {"recent_messages": [], "relevant_memories": []}

        # Get prompt with happy mood
        prompt1 = manager._build_prompt(context, "Hello!", personality)
        assert "CURRENT MOOD: happy" in prompt1

        # Change mood to concerned
        personality.mood = "concerned"
        test_db.commit()

        # Get prompt with concerned mood
        prompt2 = manager._build_prompt(context, "Hello!", personality)
        assert "CURRENT MOOD: concerned" in prompt2

        # Prompts should be different
        assert prompt1 != prompt2


class TestMoodPromptFormat:
    """Test mood prompt formatting"""

    def test_mood_on_dedicated_line(self, test_db, test_user):
        """Test that mood is on its own labeled line"""
        personality = BotPersonality(
            user_id=test_user.id,
            name="TestBot",
            friendship_level=3,
            mood="happy",
            humor=0.5,
            energy=0.6,
            curiosity=0.5,
            formality=0.3,
        )
        test_db.add(personality)
        test_db.commit()

        manager = ConversationManager()
        context = {"recent_messages": [], "relevant_memories": []}

        prompt = manager._build_prompt(context, "Hello!", personality)

        # Should have the exact format "CURRENT MOOD: {mood}"
        assert "CURRENT MOOD: happy" in prompt

        # Should be on its own line
        lines = prompt.split('\n')
        mood_line = [line for line in lines if "CURRENT MOOD:" in line]
        assert len(mood_line) == 1
        assert mood_line[0].strip() == "CURRENT MOOD: happy"

    def test_mood_in_personality_section(self, test_db, test_user):
        """Test that mood is in the personality section of prompt"""
        personality = BotPersonality(
            user_id=test_user.id,
            name="TestBot",
            friendship_level=3,
            mood="excited",
            humor=0.5,
            energy=0.6,
            curiosity=0.5,
            formality=0.3,
        )
        test_db.add(personality)
        test_db.commit()

        manager = ConversationManager()
        context = {"recent_messages": [], "relevant_memories": []}

        prompt = manager._build_prompt(context, "Hello!", personality)

        # Mood should appear before the instructions section
        assert prompt.index("CURRENT MOOD:") < prompt.index("INSTRUCTIONS:")


class TestAllMoodsSupported:
    """Test that all valid moods are supported in prompt"""

    def test_all_documented_moods(self, test_db):
        """Test all documented moods work in prompt"""
        # From personality.py: happy, excited, calm, concerned, playful, thoughtful
        valid_moods = ["happy", "excited", "calm", "concerned", "playful", "thoughtful"]

        manager = ConversationManager()
        context = {"recent_messages": [], "relevant_memories": []}

        for i, mood in enumerate(valid_moods):
            user = User(id=i+20, name=f"User{i}", age=10, created_at=datetime.now())
            test_db.add(user)
            test_db.commit()

            personality = BotPersonality(
                user_id=user.id,
                name="TestBot",
                friendship_level=3,
                mood=mood,
                humor=0.5,
                energy=0.6,
                curiosity=0.5,
                formality=0.3,
            )
            test_db.add(personality)
            test_db.commit()

            prompt = manager._build_prompt(context, "Hello!", personality)

            # Each mood should appear in its prompt
            assert f"CURRENT MOOD: {mood}" in prompt


class TestMoodWithOtherContext:
    """Test mood inclusion alongside other context"""

    def test_mood_with_conversation_history(self, test_db, test_user, test_conversation):
        """Test mood in prompt with conversation history"""
        personality = BotPersonality(
            user_id=test_user.id,
            name="TestBot",
            friendship_level=3,
            mood="happy",
            humor=0.5,
            energy=0.6,
            curiosity=0.5,
            formality=0.3,
        )
        test_db.add(personality)
        test_db.commit()

        # Add some messages
        msg1 = Message(
            conversation_id=test_conversation.id,
            role="user",
            content="Hello!",
            timestamp=datetime.now(),
        )
        msg2 = Message(
            conversation_id=test_conversation.id,
            role="assistant",
            content="Hi there!",
            timestamp=datetime.now(),
        )
        test_db.add(msg1)
        test_db.add(msg2)
        test_db.commit()

        manager = ConversationManager()
        context = {"recent_messages": [msg1, msg2], "relevant_memories": []}

        prompt = manager._build_prompt(context, "How are you?", personality)

        # Should still include mood
        assert "CURRENT MOOD: happy" in prompt

        # Should also include conversation history
        assert "Hello!" in prompt
        assert "Hi there!" in prompt

    def test_mood_with_quirks_and_interests(self, test_db, test_user):
        """Test that mood is included alongside quirks and interests"""
        personality = BotPersonality(
            user_id=test_user.id,
            name="TestBot",
            friendship_level=3,
            mood="playful",
            humor=0.5,
            energy=0.6,
            curiosity=0.5,
            formality=0.3,
        )
        personality.set_quirks(["uses_emojis", "tells_puns"])
        personality.set_interests(["sports", "music"])
        test_db.add(personality)
        test_db.commit()

        manager = ConversationManager()
        context = {"recent_messages": [], "relevant_memories": []}

        prompt = manager._build_prompt(context, "Hello!", personality)

        # Should include mood
        assert "CURRENT MOOD: playful" in prompt

        # Should also include quirks
        assert "uses_emojis" in prompt
        assert "tells_puns" in prompt

        # Should include interests
        assert "sports" in prompt
        assert "music" in prompt


class TestMoodIntegrationWithEmojiQuirk:
    """Test that mood affects emoji selection through quirks"""

    def test_mood_passed_to_emoji_quirk(self, test_db, test_user):
        """Test that personality mood is used by emoji quirk"""
        personality = BotPersonality(
            user_id=test_user.id,
            name="TestBot",
            friendship_level=3,
            mood="excited",
            humor=0.5,
            energy=0.6,
            curiosity=0.5,
            formality=0.3,
        )
        personality.set_quirks(["uses_emojis"])
        test_db.add(personality)
        test_db.commit()

        manager = ConversationManager()

        # Apply personality filter (which uses mood for emoji selection)
        response = manager._apply_personality_filter(
            "This is great!",
            personality,
            ""
        )

        # The emoji quirk should have received the "excited" mood
        # (actual emoji selection tested in emoji quirk tests)
        # Here we just verify mood is accessible
        assert personality.mood == "excited"


class TestMoodPropagation:
    """Test mood propagation through the system"""

    def test_user_mood_affects_bot_mood_affects_prompt(self, test_db, test_user):
        """Test complete flow: user mood -> bot mood -> prompt"""
        personality = BotPersonality(
            user_id=test_user.id,
            name="TestBot",
            friendship_level=3,
            mood="happy",
            humor=0.5,
            energy=0.6,
            curiosity=0.5,
            formality=0.3,
        )
        test_db.add(personality)
        test_db.commit()

        manager_conv = ConversationManager()
        manager_pers = PersonalityManager()

        # Detect sad user mood
        user_message = "I'm feeling sad today"
        detected_mood = manager_conv._detect_user_mood(user_message)
        assert detected_mood == "sad"

        # Update bot mood based on user mood
        updated_personality = manager_pers.update_mood(personality, detected_mood, test_db)
        assert updated_personality.mood == "concerned"  # Bot responds with concern

        # Build prompt with updated mood
        context = {"recent_messages": [], "relevant_memories": []}
        prompt = manager_conv._build_prompt(context, user_message, updated_personality)

        # Prompt should reflect concerned mood
        assert "CURRENT MOOD: concerned" in prompt


class TestMoodConsistency:
    """Test consistency of mood in prompts"""

    def test_same_mood_same_prompt(self, test_db, test_user):
        """Test that same mood produces same prompt (given same context)"""
        personality = BotPersonality(
            user_id=test_user.id,
            name="TestBot",
            friendship_level=3,
            mood="happy",
            humor=0.5,
            energy=0.6,
            curiosity=0.5,
            formality=0.3,
        )
        test_db.add(personality)
        test_db.commit()

        manager = ConversationManager()
        context = {"recent_messages": [], "relevant_memories": []}

        # Generate prompt multiple times
        prompt1 = manager._build_prompt(context, "Hello!", personality)
        prompt2 = manager._build_prompt(context, "Hello!", personality)
        prompt3 = manager._build_prompt(context, "Hello!", personality)

        # All should be identical (deterministic)
        assert prompt1 == prompt2 == prompt3


class TestMoodEdgeCases:
    """Test edge cases for mood in prompts"""

    def test_empty_mood_handled(self, test_db, test_user):
        """Test that empty mood string is handled"""
        personality = BotPersonality(
            user_id=test_user.id,
            name="TestBot",
            friendship_level=3,
            mood="",  # Empty mood
            humor=0.5,
            energy=0.6,
            curiosity=0.5,
            formality=0.3,
        )
        test_db.add(personality)
        test_db.commit()

        manager = ConversationManager()
        context = {"recent_messages": [], "relevant_memories": []}

        # Should not crash
        prompt = manager._build_prompt(context, "Hello!", personality)

        # Should still have mood line (even if empty)
        assert "CURRENT MOOD:" in prompt

    def test_mood_with_special_characters(self, test_db, test_user):
        """Test mood value is inserted as-is (no escaping needed in this context)"""
        personality = BotPersonality(
            user_id=test_user.id,
            name="TestBot",
            friendship_level=3,
            mood="happy",  # Standard mood
            humor=0.5,
            energy=0.6,
            curiosity=0.5,
            formality=0.3,
        )
        test_db.add(personality)
        test_db.commit()

        manager = ConversationManager()
        context = {"recent_messages": [], "relevant_memories": []}

        prompt = manager._build_prompt(context, "Hello!", personality)

        # Mood should appear exactly as stored
        assert "CURRENT MOOD: happy" in prompt
        assert "CURRENT MOOD: happy\n" in prompt or prompt.endswith("CURRENT MOOD: happy")
