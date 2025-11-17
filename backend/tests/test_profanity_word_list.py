"""
Tests for Profanity Word List Service
Comprehensive tests for age-appropriate profanity filtering
"""

import pytest
from services.profanity_word_list import (
    ProfanityWordList,
    profanity_word_list,
    is_profanity,
    contains_profanity,
    get_severity,
    find_profanity_words,
    censor_text,
    get_stats,
)


class TestWordListInitialization:
    """Test word list initialization and structure"""

    def test_word_list_initialized(self):
        """Test that word list is properly initialized"""
        word_list = ProfanityWordList()

        assert len(word_list.mild_words) > 0
        assert len(word_list.moderate_words) > 0
        assert len(word_list.severe_words) > 0
        assert len(word_list.variations) > 0

    def test_all_words_combined(self):
        """Test that all_words contains all categories"""
        word_list = ProfanityWordList()

        total_unique = (
            word_list.mild_words
            | word_list.moderate_words
            | word_list.severe_words
            | word_list.variations
        )

        assert len(word_list.all_words) == len(total_unique)

    def test_no_duplicate_words(self):
        """Test that there are no duplicate words across categories"""
        word_list = ProfanityWordList()

        # All_words should be a set (no duplicates)
        assert len(word_list.all_words) == len(set(word_list.all_words))

    def test_exceptions_defined(self):
        """Test that exceptions list is defined"""
        word_list = ProfanityWordList()

        assert len(word_list.exceptions) > 0
        assert "class" in word_list.exceptions
        assert "assignment" in word_list.exceptions


class TestIsProfanity:
    """Test is_profanity function"""

    def test_mild_profanity_detected(self):
        """Test detection of mild profanity"""
        assert is_profanity("damn")
        assert is_profanity("hell")
        assert is_profanity("crap")
        assert is_profanity("stupid")
        assert is_profanity("idiot")

    def test_moderate_profanity_detected(self):
        """Test detection of moderate profanity"""
        assert is_profanity("ass")
        assert is_profanity("piss")
        assert is_profanity("bitch")

    def test_severe_profanity_detected(self):
        """Test detection of severe profanity"""
        assert is_profanity("fuck")
        assert is_profanity("shit")

    def test_case_insensitive(self):
        """Test that detection is case insensitive"""
        assert is_profanity("DAMN")
        assert is_profanity("HeLl")
        assert is_profanity("CrAp")

    def test_with_whitespace(self):
        """Test detection with surrounding whitespace"""
        assert is_profanity("  damn  ")
        assert is_profanity("\thell\n")

    def test_clean_words_not_profanity(self):
        """Test that clean words are not detected"""
        assert not is_profanity("hello")
        assert not is_profanity("world")
        assert not is_profanity("friend")
        assert not is_profanity("happy")

    def test_exceptions_not_flagged(self):
        """Test that exception words are not flagged"""
        assert not is_profanity("class")
        assert not is_profanity("classic")
        assert not is_profanity("assignment")
        assert not is_profanity("glass")
        assert not is_profanity("bass")


class TestGetSeverity:
    """Test get_severity function"""

    def test_mild_severity(self):
        """Test getting severity for mild words"""
        assert get_severity("damn") == "mild"
        assert get_severity("hell") == "mild"
        assert get_severity("stupid") == "mild"

    def test_moderate_severity(self):
        """Test getting severity for moderate words"""
        assert get_severity("ass") == "moderate"
        assert get_severity("piss") == "moderate"
        assert get_severity("bitch") == "moderate"

    def test_severe_severity(self):
        """Test getting severity for severe words"""
        assert get_severity("fuck") == "severe"
        assert get_severity("shit") == "severe"

    def test_variations_severity(self):
        """Test that variations are marked as severe"""
        word_list = ProfanityWordList()

        # Variations should be considered severe
        for variation in ["f**k", "sh1t", "b1tch"]:
            severity = word_list.get_severity(variation)
            assert severity == "severe", f"{variation} should be severe"

    def test_clean_word_severity_none(self):
        """Test that clean words have severity 'none'"""
        assert get_severity("hello") == "none"
        assert get_severity("friend") == "none"
        assert get_severity("class") == "none"


class TestContainsProfanity:
    """Test contains_profanity function"""

    def test_detects_profanity_in_sentence(self):
        """Test detection of profanity in full sentences"""
        assert contains_profanity("This is damn good")
        assert contains_profanity("What the hell is this")
        assert contains_profanity("That's so stupid")

    def test_detects_multiple_word_phrases(self):
        """Test detection of multi-word profanity"""
        assert contains_profanity("Just shut up already")
        assert contains_profanity("shut up and listen")

    def test_clean_sentences_not_flagged(self):
        """Test that clean sentences are not flagged"""
        assert not contains_profanity("Hello, how are you?")
        assert not contains_profanity("I love learning!")
        assert not contains_profanity("This is awesome!")

    def test_profanity_with_punctuation(self):
        """Test detection with punctuation"""
        assert contains_profanity("Damn!")
        assert contains_profanity("What the hell?")
        assert contains_profanity("That's stupid.")

    def test_profanity_in_middle_of_sentence(self):
        """Test detection in middle of sentence"""
        assert contains_profanity("I think that's really stupid honestly")
        assert contains_profanity("This damn thing won't work")

    def test_exception_words_in_context(self):
        """Test that exception words don't trigger false positives"""
        assert not contains_profanity("I have class tomorrow")
        assert not contains_profanity("That's a classic movie")
        assert not contains_profanity("I need to do my assignment")
        assert not contains_profanity("Pass me the glass")


class TestFindProfanityWords:
    """Test find_profanity_words function"""

    def test_find_single_word(self):
        """Test finding single profanity word"""
        result = find_profanity_words("This is damn good")

        assert len(result) == 1
        assert result[0]["word"] == "damn"
        assert result[0]["severity"] == "mild"

    def test_find_multiple_words(self):
        """Test finding multiple profanity words"""
        result = find_profanity_words("This damn thing is stupid")

        assert len(result) == 2
        assert any(item["word"] == "damn" for item in result)
        assert any(item["word"] == "stupid" for item in result)

    def test_find_multi_word_phrase(self):
        """Test finding multi-word profanity phrase"""
        result = find_profanity_words("Please shut up now")

        assert len(result) >= 1
        assert any(item["word"] == "shut up" for item in result)

    def test_find_nothing_in_clean_text(self):
        """Test finding nothing in clean text"""
        result = find_profanity_words("Hello friend, how are you?")

        assert len(result) == 0

    def test_find_with_severity_levels(self):
        """Test that found words include correct severity"""
        result = find_profanity_words("damn shit stupid")

        # Should find all three with appropriate severities
        assert len(result) >= 3

        damn_item = next((item for item in result if item["word"] == "damn"), None)
        assert damn_item is not None
        assert damn_item["severity"] == "mild"

        shit_item = next((item for item in result if item["word"] == "shit"), None)
        assert shit_item is not None
        assert shit_item["severity"] == "severe"


class TestCensorText:
    """Test censor_text function"""

    def test_censor_single_word(self):
        """Test censoring single profanity word"""
        result = censor_text("This is damn good")

        assert "damn" not in result.lower()
        assert "***" in result
        assert result == "This is *** good"

    def test_censor_multiple_words(self):
        """Test censoring multiple words"""
        result = censor_text("This damn thing is stupid")

        assert "damn" not in result.lower()
        assert "stupid" not in result.lower()
        assert result.count("***") >= 2

    def test_censor_with_custom_replacement(self):
        """Test censoring with custom replacement"""
        result = censor_text("This is damn good", replacement="[censored]")

        assert "[censored]" in result
        assert "damn" not in result.lower()

    def test_censor_preserves_clean_text(self):
        """Test that clean text is preserved"""
        original = "Hello friend, how are you?"
        result = censor_text(original)

        assert result == original

    def test_censor_case_insensitive(self):
        """Test that censoring works regardless of case"""
        result1 = censor_text("DAMN this is bad")
        result2 = censor_text("damn this is bad")
        result3 = censor_text("Damn this is bad")

        # All should censor the word
        assert "damn" not in result1.lower()
        assert "damn" not in result2.lower()
        assert "damn" not in result3.lower()

    def test_censor_multi_word_phrase(self):
        """Test censoring multi-word phrases"""
        result = censor_text("Just shut up already")

        assert "shut up" not in result.lower()
        assert "***" in result


class TestGetWordsBySeverity:
    """Test get_words_by_severity function"""

    def test_get_mild_words(self):
        """Test getting mild words"""
        word_list = ProfanityWordList()
        mild = word_list.get_words_by_severity("mild")

        assert len(mild) > 0
        assert "damn" in mild
        assert "hell" in mild
        assert "stupid" in mild

    def test_get_moderate_words(self):
        """Test getting moderate words"""
        word_list = ProfanityWordList()
        moderate = word_list.get_words_by_severity("moderate")

        assert len(moderate) > 0
        assert "ass" in moderate
        assert "piss" in moderate

    def test_get_severe_words(self):
        """Test getting severe words"""
        word_list = ProfanityWordList()
        severe = word_list.get_words_by_severity("severe")

        assert len(severe) > 0
        assert "fuck" in severe
        assert "shit" in severe

    def test_get_invalid_severity(self):
        """Test getting words with invalid severity"""
        word_list = ProfanityWordList()
        result = word_list.get_words_by_severity("invalid")

        assert len(result) == 0

    def test_returned_sets_are_copies(self):
        """Test that returned sets are copies (not references)"""
        word_list = ProfanityWordList()

        mild1 = word_list.get_words_by_severity("mild")
        mild2 = word_list.get_words_by_severity("mild")

        # Modify one
        mild1.add("test_word")

        # Other should be unchanged
        assert "test_word" not in mild2


class TestGetAllWords:
    """Test get_all_words function"""

    def test_get_all_words_returns_set(self):
        """Test that get_all_words returns a set"""
        word_list = ProfanityWordList()
        all_words = word_list.get_all_words()

        assert isinstance(all_words, set)

    def test_get_all_words_is_copy(self):
        """Test that returned set is a copy"""
        word_list = ProfanityWordList()

        all1 = word_list.get_all_words()
        all2 = word_list.get_all_words()

        # Modify one
        all1.add("test_word")

        # Other should be unchanged
        assert "test_word" not in all2

    def test_get_all_words_contains_all_categories(self):
        """Test that all_words contains words from all categories"""
        word_list = ProfanityWordList()
        all_words = word_list.get_all_words()

        # Should contain mild words
        assert "damn" in all_words
        assert "stupid" in all_words

        # Should contain moderate words
        assert "ass" in all_words

        # Should contain severe words
        assert "fuck" in all_words
        assert "shit" in all_words


class TestGetStats:
    """Test get_stats function"""

    def test_stats_structure(self):
        """Test that stats returns correct structure"""
        stats = get_stats()

        assert "total" in stats
        assert "mild" in stats
        assert "moderate" in stats
        assert "severe" in stats
        assert "variations" in stats
        assert "exceptions" in stats

    def test_stats_values(self):
        """Test that stats values are reasonable"""
        stats = get_stats()

        # All should be positive integers
        assert stats["total"] > 0
        assert stats["mild"] > 0
        assert stats["moderate"] > 0
        assert stats["severe"] > 0
        assert stats["variations"] > 0
        assert stats["exceptions"] > 0

    def test_total_is_sum_of_categories(self):
        """Test that total matches sum of categories"""
        word_list = ProfanityWordList()

        # Total should equal combined unique words
        expected_total = len(
            word_list.mild_words
            | word_list.moderate_words
            | word_list.severe_words
            | word_list.variations
        )

        stats = word_list.get_stats()
        assert stats["total"] == expected_total


class TestVariationsAndLeetspeak:
    """Test variations and leetspeak detection"""

    def test_leetspeak_detected(self):
        """Test that leetspeak variations are detected"""
        word_list = ProfanityWordList()

        # These should be in variations
        assert contains_profanity("d4mn")
        assert contains_profanity("h3ll")
        assert contains_profanity("sh1t")

    def test_asterisk_censoring_detected(self):
        """Test that self-censored versions are detected"""
        word_list = ProfanityWordList()

        assert contains_profanity("d*mn")
        assert contains_profanity("h*ll")
        assert contains_profanity("f**k")

    def test_spacing_tricks_detected(self):
        """Test that spacing tricks are detected"""
        word_list = ProfanityWordList()

        assert contains_profanity("d a m n")
        assert contains_profanity("h e l l")

    def test_common_misspellings_detected(self):
        """Test that common misspellings are detected"""
        word_list = ProfanityWordList()

        assert contains_profanity("damm")
        assert contains_profanity("fuk")


class TestEdgeCases:
    """Test edge cases for profanity detection"""

    def test_empty_string(self):
        """Test detection with empty string"""
        assert not contains_profanity("")
        assert get_severity("") == "none"

    def test_single_character(self):
        """Test detection with single character"""
        assert not contains_profanity("a")
        assert not is_profanity("a")

    def test_very_long_text(self):
        """Test detection in very long text"""
        long_text = "hello " * 1000 + "damn" + " world" * 1000

        assert contains_profanity(long_text)

    def test_unicode_characters(self):
        """Test handling of unicode characters"""
        # Should not crash with unicode
        result = contains_profanity("Hello 你好 world")
        assert isinstance(result, bool)

    def test_special_characters_only(self):
        """Test text with only special characters"""
        assert not contains_profanity("@#$%^&*()")
        assert not contains_profanity("!!!")

    def test_numbers_only(self):
        """Test text with only numbers"""
        assert not contains_profanity("123456")
        assert not contains_profanity("42")


class TestAgeAppropriate:
    """Test that word list is age-appropriate for kids 8-14"""

    def test_focuses_on_common_kid_profanity(self):
        """Test that list includes common words kids use"""
        # These are words kids commonly use and should be filtered
        assert is_profanity("stupid")
        assert is_profanity("dumb")
        assert is_profanity("idiot")
        assert is_profanity("shut up")

    def test_includes_educational_words(self):
        """Test that list helps teach appropriate language"""
        word_list = ProfanityWordList()

        # Should include words for educational purposes
        assert "damn" in word_list.mild_words
        assert "crap" in word_list.mild_words

    def test_exceptions_prevent_over_filtering(self):
        """Test that exceptions prevent false positives in education"""
        # Educational words shouldn't be flagged
        assert not is_profanity("class")
        assert not is_profanity("assignment")
        assert not is_profanity("classic")

        # Should work in context
        assert not contains_profanity("I have a class assignment")


class TestConvenienceFunctions:
    """Test convenience wrapper functions"""

    def test_is_profanity_convenience(self):
        """Test is_profanity convenience function"""
        assert is_profanity("damn")
        assert not is_profanity("hello")

    def test_contains_profanity_convenience(self):
        """Test contains_profanity convenience function"""
        assert contains_profanity("This is damn good")
        assert not contains_profanity("This is really good")

    def test_get_severity_convenience(self):
        """Test get_severity convenience function"""
        assert get_severity("damn") == "mild"
        assert get_severity("shit") == "severe"
        assert get_severity("hello") == "none"

    def test_find_profanity_words_convenience(self):
        """Test find_profanity_words convenience function"""
        result = find_profanity_words("damn this")
        assert len(result) >= 1

    def test_censor_text_convenience(self):
        """Test censor_text convenience function"""
        result = censor_text("damn this")
        assert "***" in result

    def test_get_stats_convenience(self):
        """Test get_stats convenience function"""
        stats = get_stats()
        assert "total" in stats

    def test_convenience_functions_match_class_methods(self):
        """Test that convenience functions match class method behavior"""
        word_list = ProfanityWordList()

        # is_profanity
        assert is_profanity("damn") == word_list.is_profanity("damn")

        # contains_profanity
        text = "This is damn good"
        assert contains_profanity(text) == word_list.contains_profanity(text)

        # get_severity
        assert get_severity("shit") == word_list.get_severity("shit")


class TestConsistency:
    """Test consistency across different methods"""

    def test_is_profanity_matches_contains(self):
        """Test that is_profanity and contains_profanity are consistent"""
        test_words = ["damn", "hell", "stupid", "hello", "world"]

        for word in test_words:
            is_prof = is_profanity(word)
            contains = contains_profanity(word)

            # If it's profanity, contains should also be True
            if is_prof:
                assert contains, f"{word} should be detected by both methods"

    def test_severity_consistent_with_detection(self):
        """Test that severity is consistent with detection"""
        test_words = ["damn", "shit", "hello"]

        for word in test_words:
            is_prof = is_profanity(word)
            severity = get_severity(word)

            if is_prof:
                assert severity != "none", f"{word} should have non-none severity"
            else:
                assert severity == "none", f"{word} should have none severity"

    def test_find_consistent_with_contains(self):
        """Test that find_profanity_words is consistent with contains_profanity"""
        texts = [
            "This is damn good",
            "Hello world",
            "What the hell",
            "I love learning",
        ]

        for text in texts:
            contains = contains_profanity(text)
            found = find_profanity_words(text)

            if contains:
                assert len(found) > 0, f"Should find words in: {text}"
            else:
                assert len(found) == 0, f"Should find nothing in: {text}"
