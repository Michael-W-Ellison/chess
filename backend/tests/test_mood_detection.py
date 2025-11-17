"""
Tests for Mood Detection from User Messages
Tests the keyword-based mood detection system
"""

import pytest
from services.conversation_manager import ConversationManager


class TestMoodDetectionBasics:
    """Test basic mood detection from messages"""

    def test_detect_sad_with_sad_keyword(self):
        """Test detection of sad mood with 'sad' keyword"""
        manager = ConversationManager()

        assert manager._detect_user_mood("I'm sad") == "sad"
        assert manager._detect_user_mood("I feel sad today") == "sad"
        assert manager._detect_user_mood("This makes me sad") == "sad"

    def test_detect_sad_with_upset_keyword(self):
        """Test detection of sad mood with 'upset' keyword"""
        manager = ConversationManager()

        assert manager._detect_user_mood("I'm upset") == "sad"
        assert manager._detect_user_mood("I'm really upset about this") == "sad"
        assert manager._detect_user_mood("That's so upsetting") == "sad"

    def test_detect_sad_with_crying_keyword(self):
        """Test detection of sad mood with 'crying' keyword"""
        manager = ConversationManager()

        assert manager._detect_user_mood("I'm crying") == "sad"
        assert manager._detect_user_mood("I've been crying all day") == "sad"
        assert manager._detect_user_mood("I can't stop crying") == "sad"

    def test_detect_sad_with_depressed_keyword(self):
        """Test detection of sad mood with 'depressed' keyword"""
        manager = ConversationManager()

        assert manager._detect_user_mood("I feel depressed") == "sad"
        assert manager._detect_user_mood("I'm so depressed") == "sad"
        assert manager._detect_user_mood("I'm depressed about this") == "sad"


class TestAnxiousMoodDetection:
    """Test anxious mood detection"""

    def test_detect_anxious_with_worried_keyword(self):
        """Test detection of anxious mood with 'worried' keyword"""
        manager = ConversationManager()

        assert manager._detect_user_mood("I'm worried") == "anxious"
        assert manager._detect_user_mood("I'm worried about the test") == "anxious"
        assert manager._detect_user_mood("I feel worried today") == "anxious"

    def test_detect_anxious_with_nervous_keyword(self):
        """Test detection of anxious mood with 'nervous' keyword"""
        manager = ConversationManager()

        assert manager._detect_user_mood("I'm nervous") == "anxious"
        assert manager._detect_user_mood("I feel so nervous") == "anxious"
        assert manager._detect_user_mood("That makes me nervous") == "anxious"

    def test_detect_anxious_with_scared_keyword(self):
        """Test detection of anxious mood with 'scared' keyword"""
        manager = ConversationManager()

        assert manager._detect_user_mood("I'm scared") == "anxious"
        assert manager._detect_user_mood("I'm so scared of failing") == "anxious"
        assert manager._detect_user_mood("I feel scared about this") == "anxious"

    def test_detect_anxious_with_anxious_keyword(self):
        """Test detection of anxious mood with 'anxious' keyword"""
        manager = ConversationManager()

        assert manager._detect_user_mood("I'm anxious") == "anxious"
        assert manager._detect_user_mood("Feeling anxious today") == "anxious"
        assert manager._detect_user_mood("This makes me anxious") == "anxious"


class TestHappyMoodDetection:
    """Test happy mood detection"""

    def test_detect_happy_with_happy_keyword(self):
        """Test detection of happy mood with 'happy' keyword"""
        manager = ConversationManager()

        assert manager._detect_user_mood("I'm happy") == "happy"
        assert manager._detect_user_mood("I'm so happy!") == "happy"
        assert manager._detect_user_mood("This makes me happy") == "happy"

    def test_detect_happy_with_excited_keyword(self):
        """Test detection of happy mood with 'excited' keyword"""
        manager = ConversationManager()

        assert manager._detect_user_mood("I'm excited") == "happy"
        assert manager._detect_user_mood("I'm so excited about this!") == "happy"
        assert manager._detect_user_mood("I feel excited today") == "happy"

    def test_detect_happy_with_great_keyword(self):
        """Test detection of happy mood with 'great' keyword"""
        manager = ConversationManager()

        assert manager._detect_user_mood("That's great!") == "happy"
        assert manager._detect_user_mood("This is great") == "happy"
        assert manager._detect_user_mood("I feel great") == "happy"

    def test_detect_happy_with_awesome_keyword(self):
        """Test detection of happy mood with 'awesome' keyword"""
        manager = ConversationManager()

        assert manager._detect_user_mood("That's awesome!") == "happy"
        assert manager._detect_user_mood("This is awesome") == "happy"
        assert manager._detect_user_mood("You're awesome") == "happy"


class TestAngryMoodDetection:
    """Test angry mood detection"""

    def test_detect_angry_with_angry_keyword(self):
        """Test detection of angry mood with 'angry' keyword"""
        manager = ConversationManager()

        assert manager._detect_user_mood("I'm angry") == "angry"
        assert manager._detect_user_mood("I'm so angry about this") == "angry"
        assert manager._detect_user_mood("That makes me angry") == "angry"

    def test_detect_angry_with_mad_keyword(self):
        """Test detection of angry mood with 'mad' keyword"""
        manager = ConversationManager()

        assert manager._detect_user_mood("I'm mad") == "angry"
        assert manager._detect_user_mood("I'm so mad right now") == "angry"
        assert manager._detect_user_mood("That's maddening") == "angry"

    def test_detect_angry_with_furious_keyword(self):
        """Test detection of angry mood with 'furious' keyword"""
        manager = ConversationManager()

        assert manager._detect_user_mood("I'm furious") == "angry"
        assert manager._detect_user_mood("I'm absolutely furious") == "angry"
        assert manager._detect_user_mood("This makes me furious") == "angry"


class TestNeutralMoodDetection:
    """Test neutral mood detection (default)"""

    def test_detect_neutral_with_no_keywords(self):
        """Test that messages without emotional keywords return neutral"""
        manager = ConversationManager()

        assert manager._detect_user_mood("What's the weather?") == "neutral"
        assert manager._detect_user_mood("Tell me about math") == "neutral"
        assert manager._detect_user_mood("How do I solve this?") == "neutral"

    def test_detect_neutral_with_factual_questions(self):
        """Test neutral detection for factual questions"""
        manager = ConversationManager()

        assert manager._detect_user_mood("What time is it?") == "neutral"
        assert manager._detect_user_mood("Where is the library?") == "neutral"
        assert manager._detect_user_mood("Who invented the telephone?") == "neutral"

    def test_detect_neutral_with_statements(self):
        """Test neutral detection for neutral statements"""
        manager = ConversationManager()

        assert manager._detect_user_mood("I have homework") == "neutral"
        assert manager._detect_user_mood("The book is blue") == "neutral"
        assert manager._detect_user_mood("I went to school") == "neutral"


class TestCaseInsensitivity:
    """Test that mood detection is case insensitive"""

    def test_uppercase_keywords_detected(self):
        """Test that uppercase keywords are detected"""
        manager = ConversationManager()

        assert manager._detect_user_mood("I'm HAPPY") == "happy"
        assert manager._detect_user_mood("I'm SAD") == "sad"
        assert manager._detect_user_mood("I'm WORRIED") == "anxious"
        assert manager._detect_user_mood("I'm ANGRY") == "angry"

    def test_mixed_case_keywords_detected(self):
        """Test that mixed case keywords are detected"""
        manager = ConversationManager()

        assert manager._detect_user_mood("I'm HaPpY") == "happy"
        assert manager._detect_user_mood("I'm sAd") == "sad"
        assert manager._detect_user_mood("I'm WoRrIeD") == "anxious"
        assert manager._detect_user_mood("I'm AnGrY") == "angry"

    def test_title_case_keywords_detected(self):
        """Test that title case keywords are detected"""
        manager = ConversationManager()

        assert manager._detect_user_mood("I'm Happy") == "happy"
        assert manager._detect_user_mood("I'm Sad") == "sad"
        assert manager._detect_user_mood("I'm Worried") == "anxious"
        assert manager._detect_user_mood("I'm Angry") == "angry"


class TestKeywordInContext:
    """Test keyword detection in various contexts"""

    def test_keyword_at_start_of_message(self):
        """Test detection when keyword is at start"""
        manager = ConversationManager()

        assert manager._detect_user_mood("Happy to see you!") == "happy"
        assert manager._detect_user_mood("Sad news today") == "sad"
        assert manager._detect_user_mood("Worried about tomorrow") == "anxious"

    def test_keyword_at_end_of_message(self):
        """Test detection when keyword is at end"""
        manager = ConversationManager()

        assert manager._detect_user_mood("I'm feeling happy") == "happy"
        assert manager._detect_user_mood("This makes me sad") == "sad"
        assert manager._detect_user_mood("I feel worried") == "anxious"

    def test_keyword_in_middle_of_message(self):
        """Test detection when keyword is in middle"""
        manager = ConversationManager()

        assert manager._detect_user_mood("I'm really happy about this") == "happy"
        assert manager._detect_user_mood("I'm so sad right now") == "sad"
        assert manager._detect_user_mood("I'm very worried today") == "anxious"

    def test_keyword_as_part_of_longer_word(self):
        """Test that keywords within other words are detected"""
        manager = ConversationManager()

        # "sad" in "sadness"
        assert manager._detect_user_mood("I feel sadness") == "sad"

        # "happy" in "unhappy" (still matches)
        assert manager._detect_user_mood("I'm unhappy") == "happy"

        # "upset" in "upsetting"
        assert manager._detect_user_mood("This is upsetting") == "sad"


class TestMultipleKeywords:
    """Test detection with multiple mood keywords"""

    def test_first_keyword_takes_precedence(self):
        """Test that first matching mood category wins"""
        manager = ConversationManager()

        # "sad" is checked before "happy" in the if-elif chain
        # So "sad" should win
        result = manager._detect_user_mood("I was sad but now I'm happy")
        assert result == "sad"

    def test_multiple_keywords_same_mood(self):
        """Test multiple keywords from same mood category"""
        manager = ConversationManager()

        assert manager._detect_user_mood("I'm sad and upset") == "sad"
        assert manager._detect_user_mood("I'm worried and nervous") == "anxious"
        assert manager._detect_user_mood("I'm happy and excited") == "happy"
        assert manager._detect_user_mood("I'm angry and mad") == "angry"


class TestSpecialCharacters:
    """Test mood detection with special characters"""

    def test_keywords_with_punctuation(self):
        """Test detection when keywords have punctuation"""
        manager = ConversationManager()

        assert manager._detect_user_mood("I'm happy!") == "happy"
        assert manager._detect_user_mood("I'm sad...") == "sad"
        assert manager._detect_user_mood("I'm worried?") == "anxious"
        assert manager._detect_user_mood("I'm angry!!!") == "angry"

    def test_keywords_with_emojis(self):
        """Test detection when message includes emojis"""
        manager = ConversationManager()

        assert manager._detect_user_mood("I'm happy 😊") == "happy"
        assert manager._detect_user_mood("I'm sad 😢") == "sad"
        assert manager._detect_user_mood("I'm worried 😰") == "anxious"
        assert manager._detect_user_mood("I'm angry 😡") == "angry"

    def test_keywords_with_quotes(self):
        """Test detection with quoted text"""
        manager = ConversationManager()

        assert manager._detect_user_mood("I'm 'happy' about this") == "happy"
        assert manager._detect_user_mood('I feel "sad"') == "sad"


class TestEmptyAndShortMessages:
    """Test mood detection with empty and very short messages"""

    def test_empty_message_returns_neutral(self):
        """Test that empty message returns neutral"""
        manager = ConversationManager()

        assert manager._detect_user_mood("") == "neutral"

    def test_single_word_messages(self):
        """Test single word messages"""
        manager = ConversationManager()

        assert manager._detect_user_mood("happy") == "happy"
        assert manager._detect_user_mood("sad") == "sad"
        assert manager._detect_user_mood("worried") == "anxious"
        assert manager._detect_user_mood("angry") == "angry"
        assert manager._detect_user_mood("hello") == "neutral"

    def test_very_short_messages(self):
        """Test very short messages"""
        manager = ConversationManager()

        assert manager._detect_user_mood("ok") == "neutral"
        assert manager._detect_user_mood("no") == "neutral"
        assert manager._detect_user_mood("yes") == "neutral"


class TestLongMessages:
    """Test mood detection in long messages"""

    def test_long_message_with_mood_keyword(self):
        """Test long message with mood keyword"""
        manager = ConversationManager()

        long_msg = "I went to school today and had a lot of homework. I'm feeling sad about all the work I need to do. I wish I had more time to play."
        assert manager._detect_user_mood(long_msg) == "sad"

    def test_long_message_without_mood_keyword(self):
        """Test long message without mood keywords"""
        manager = ConversationManager()

        long_msg = "Today I learned about history. We studied ancient civilizations and learned about pyramids. It was interesting to learn about different cultures."
        assert manager._detect_user_mood(long_msg) == "neutral"

    def test_story_with_emotional_keyword(self):
        """Test story containing emotional keyword"""
        manager = ConversationManager()

        story = "Once upon a time, there was a prince who lost his kingdom. He was very sad and wandered for many years."
        assert manager._detect_user_mood(story) == "sad"


class TestAllKeywordsCovered:
    """Test that all documented keywords work"""

    def test_all_sad_keywords(self):
        """Test all sad keywords: sad, upset, crying, depressed"""
        manager = ConversationManager()

        sad_keywords = ["sad", "upset", "crying", "depressed"]
        for keyword in sad_keywords:
            assert manager._detect_user_mood(f"I'm {keyword}") == "sad", f"Keyword '{keyword}' failed"

    def test_all_anxious_keywords(self):
        """Test all anxious keywords: worried, nervous, scared, anxious"""
        manager = ConversationManager()

        anxious_keywords = ["worried", "nervous", "scared", "anxious"]
        for keyword in anxious_keywords:
            assert manager._detect_user_mood(f"I'm {keyword}") == "anxious", f"Keyword '{keyword}' failed"

    def test_all_happy_keywords(self):
        """Test all happy keywords: happy, excited, great, awesome"""
        manager = ConversationManager()

        happy_keywords = ["happy", "excited", "great", "awesome"]
        for keyword in happy_keywords:
            assert manager._detect_user_mood(f"I'm {keyword}") == "happy", f"Keyword '{keyword}' failed"

    def test_all_angry_keywords(self):
        """Test all angry keywords: angry, mad, furious"""
        manager = ConversationManager()

        angry_keywords = ["angry", "mad", "furious"]
        for keyword in angry_keywords:
            assert manager._detect_user_mood(f"I'm {keyword}") == "angry", f"Keyword '{keyword}' failed"


class TestEdgeCases:
    """Test edge cases for mood detection"""

    def test_whitespace_only_message(self):
        """Test message with only whitespace"""
        manager = ConversationManager()

        assert manager._detect_user_mood("   ") == "neutral"
        assert manager._detect_user_mood("\n") == "neutral"
        assert manager._detect_user_mood("\t") == "neutral"

    def test_numbers_and_symbols(self):
        """Test message with numbers and symbols"""
        manager = ConversationManager()

        assert manager._detect_user_mood("123 456") == "neutral"
        assert manager._detect_user_mood("@#$%") == "neutral"
        assert manager._detect_user_mood("I'm happy 100%") == "happy"

    def test_repeated_keywords(self):
        """Test message with repeated keywords"""
        manager = ConversationManager()

        assert manager._detect_user_mood("sad sad sad") == "sad"
        assert manager._detect_user_mood("happy happy happy") == "happy"

    def test_negation_not_detected(self):
        """Test that negation doesn't prevent detection (current simple implementation)"""
        manager = ConversationManager()

        # Current implementation still detects keyword even with negation
        # This is a known limitation of simple keyword matching
        assert manager._detect_user_mood("I'm not sad") == "sad"
        assert manager._detect_user_mood("I'm not happy") == "happy"


class TestConsistency:
    """Test consistency of mood detection"""

    def test_same_message_same_result(self):
        """Test that same message always gives same result"""
        manager = ConversationManager()

        message = "I'm feeling happy today"
        result1 = manager._detect_user_mood(message)
        result2 = manager._detect_user_mood(message)
        result3 = manager._detect_user_mood(message)

        assert result1 == result2 == result3 == "happy"

    def test_deterministic_behavior(self):
        """Test that detection is deterministic (no randomness)"""
        manager = ConversationManager()

        messages = [
            "I'm sad",
            "I'm happy",
            "I'm worried",
            "I'm angry",
            "Hello there"
        ]

        expected = ["sad", "happy", "anxious", "angry", "neutral"]

        # Test multiple times
        for _ in range(10):
            results = [manager._detect_user_mood(msg) for msg in messages]
            assert results == expected
