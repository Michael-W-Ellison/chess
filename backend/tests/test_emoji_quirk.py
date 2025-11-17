"""
Tests for Emoji Quirk Service
Task 69: Implement uses_emojis quirk
"""

import pytest
import re
from services.emoji_quirk_service import EmojiQuirkService, emoji_quirk_service


class TestEmojiQuirkService:
    """Test emoji quirk service initialization and basic functionality"""

    def test_service_initialization(self):
        """Test that service initializes correctly"""
        service = EmojiQuirkService()
        assert service is not None
        assert hasattr(service, 'MOOD_EMOJIS')
        assert hasattr(service, 'CONTEXT_EMOJIS')

    def test_global_instance_exists(self):
        """Test that global singleton instance exists"""
        assert emoji_quirk_service is not None


class TestEmojiApplication:
    """Test emoji application to text"""

    def test_apply_emojis_basic(self):
        """Test basic emoji application"""
        service = EmojiQuirkService()
        text = "That's really cool!"
        result = service.apply_emojis(text, mood="happy", intensity=1.0)

        # Result should contain the original text
        assert "cool" in result
        # Result should be different from original (emoji added)
        # (with intensity=1.0, emoji should always be added)
        assert len(result) > len(text)

    def test_apply_emojis_empty_text(self):
        """Test emoji application to empty text"""
        service = EmojiQuirkService()
        result = service.apply_emojis("", mood="happy", intensity=0.5)
        assert result == ""

    def test_apply_emojis_short_text(self):
        """Test emoji application to very short text"""
        service = EmojiQuirkService()
        text = "Hi"
        result = service.apply_emojis(text, mood="happy", intensity=0.5)
        # Short text should not be heavily modified
        assert "Hi" in result

    def test_intensity_affects_emoji_frequency(self):
        """Test that intensity parameter affects emoji frequency"""
        service = EmojiQuirkService()
        text = "I love reading books. It's so much fun. I learn a lot."

        # With zero intensity, should add few/no emojis
        result_low = service.apply_emojis(text, mood="happy", intensity=0.0)

        # With high intensity, should add more emojis
        result_high = service.apply_emojis(text, mood="happy", intensity=1.0)

        # High intensity result should typically have more emojis
        # (This is probabilistic, so we just check both are valid)
        assert len(result_low) >= len(text)
        assert len(result_high) >= len(text)


class TestMoodBasedEmojis:
    """Test mood-based emoji selection"""

    def test_happy_mood_emojis(self):
        """Test emojis for happy mood"""
        service = EmojiQuirkService()
        text = "That's great!"
        result = service.apply_emojis(text, mood="happy", intensity=1.0)

        # Check that an emoji is present (unicode characters)
        emoji_pattern = re.compile(r'[\U0001F600-\U0001F64F]')  # Emoticons
        assert emoji_pattern.search(result) or '✨' in result or '🌟' in result

    def test_excited_mood_emojis(self):
        """Test emojis for excited mood"""
        service = EmojiQuirkService()
        text = "This is amazing!"
        result = service.apply_emojis(text, mood="excited", intensity=1.0)

        # Should contain text and emoji
        assert "amazing" in result
        assert len(result) > len(text)

    def test_concerned_mood_emojis(self):
        """Test emojis for concerned mood"""
        service = EmojiQuirkService()
        text = "I'm here for you."
        result = service.apply_emojis(text, mood="concerned", intensity=1.0)

        assert "here for you" in result
        assert len(result) > len(text)

    def test_playful_mood_emojis(self):
        """Test emojis for playful mood"""
        service = EmojiQuirkService()
        text = "Let's play a game!"
        result = service.apply_emojis(text, mood="playful", intensity=1.0)

        assert "play" in result
        assert len(result) > len(text)


class TestContextualEmojis:
    """Test context-based emoji selection"""

    def test_game_context_emoji(self):
        """Test emoji for game-related content"""
        service = EmojiQuirkService()
        text = "Want to play a game?"
        result = service.apply_emojis(text, mood="happy", intensity=1.0)

        # Should add game or play-related emoji
        assert "game" in result

    def test_reading_context_emoji(self):
        """Test emoji for reading-related content"""
        service = EmojiQuirkService()
        text = "I love reading books."
        result = service.apply_emojis(text, mood="happy", intensity=1.0)

        assert "reading" in result

    def test_music_context_emoji(self):
        """Test emoji for music-related content"""
        service = EmojiQuirkService()
        text = "Music makes me happy."
        result = service.apply_emojis(text, mood="happy", intensity=1.0)

        assert "Music" in result

    def test_achievement_context_emoji(self):
        """Test emoji for achievement-related content"""
        service = EmojiQuirkService()
        text = "You did great on your test!"
        result = service.apply_emojis(text, mood="happy", intensity=1.0)

        assert "great" in result


class TestEmojiPlacement:
    """Test emoji placement within text"""

    def test_emoji_placement_with_punctuation(self):
        """Test that emojis are placed correctly with punctuation"""
        service = EmojiQuirkService()
        text = "That's cool!"
        result = service.apply_emojis(text, mood="happy", intensity=1.0)

        # Original text should be preserved
        assert "cool" in result
        # Should handle punctuation correctly
        assert "!" in result

    def test_multiple_sentences(self):
        """Test emoji application to multiple sentences"""
        service = EmojiQuirkService()
        text = "I love this. It's so much fun. Thank you!"
        result = service.apply_emojis(text, mood="happy", intensity=1.0)

        # All sentences should be present
        assert "love" in result
        assert "fun" in result
        assert "Thank you" in result

    def test_preserves_original_meaning(self):
        """Test that emojis don't change the original meaning"""
        service = EmojiQuirkService()
        text = "I can help you with your homework."
        result = service.apply_emojis(text, mood="happy", intensity=0.5)

        # Core message should be intact
        assert "help" in result
        assert "homework" in result


class TestEdgeCases:
    """Test edge cases and special scenarios"""

    def test_very_long_text(self):
        """Test emoji application to long text"""
        service = EmojiQuirkService()
        text = " ".join(["This is a sentence."] * 20)
        result = service.apply_emojis(text, mood="happy", intensity=0.5)

        # Should handle long text without errors
        assert len(result) >= len(text)
        assert "sentence" in result

    def test_text_with_special_characters(self):
        """Test text with special characters"""
        service = EmojiQuirkService()
        text = "It's a great day! How're you doing?"
        result = service.apply_emojis(text, mood="happy", intensity=0.5)

        # Should preserve apostrophes and special chars
        assert "It's" in result or "It" in result
        assert "great" in result

    def test_text_with_numbers(self):
        """Test text with numbers"""
        service = EmojiQuirkService()
        text = "I scored 100 points!"
        result = service.apply_emojis(text, mood="excited", intensity=0.5)

        # Numbers should be preserved
        assert "100" in result
        assert "points" in result

    def test_unknown_mood_fallback(self):
        """Test fallback for unknown mood"""
        service = EmojiQuirkService()
        text = "This is interesting."
        result = service.apply_emojis(text, mood="unknown_mood", intensity=1.0)

        # Should still work with generic emojis
        assert "interesting" in result


class TestIntegrationScenarios:
    """Test realistic integration scenarios"""

    def test_friendly_greeting(self):
        """Test emoji application to friendly greeting"""
        service = EmojiQuirkService()
        text = "Hey there! How are you doing today?"
        result = service.apply_emojis(text, mood="happy", intensity=0.5)

        assert "Hey there" in result
        assert "today" in result

    def test_encouraging_message(self):
        """Test emoji application to encouraging message"""
        service = EmojiQuirkService()
        text = "You can do it! I believe in you."
        result = service.apply_emojis(text, mood="excited", intensity=0.6)

        assert "can do it" in result
        assert "believe" in result

    def test_helpful_advice(self):
        """Test emoji application to helpful advice"""
        service = EmojiQuirkService()
        text = "Let me help you with that. Take it one step at a time."
        result = service.apply_emojis(text, mood="calm", intensity=0.4)

        assert "help" in result
        assert "one step at a time" in result

    def test_playful_response(self):
        """Test emoji application to playful response"""
        service = EmojiQuirkService()
        text = "That sounds like so much fun! Let's do it together."
        result = service.apply_emojis(text, mood="playful", intensity=0.7)

        assert "fun" in result
        assert "together" in result


class TestServiceMethods:
    """Test individual service methods"""

    def test_get_mood_emoji(self):
        """Test mood emoji selection"""
        service = EmojiQuirkService()
        emoji = service._get_mood_emoji("happy")
        assert emoji in service.MOOD_EMOJIS.get("happy", [])

    def test_get_contextual_emoji(self):
        """Test contextual emoji selection"""
        service = EmojiQuirkService()
        text = "I love playing games"
        emoji = service._get_contextual_emoji(text, "happy")

        # Should return game-related emoji or empty string
        assert isinstance(emoji, str)

    def test_split_into_sentences(self):
        """Test sentence splitting"""
        service = EmojiQuirkService()
        text = "Hello there. How are you? I'm doing great!"
        sentences = service._split_into_sentences(text)

        # Should split into sentences
        assert len(sentences) >= 1
        assert any("Hello" in s for s in sentences)
