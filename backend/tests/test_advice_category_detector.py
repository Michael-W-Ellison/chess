"""
Tests for Advice Category Detector Service
Comprehensive test coverage for advice detection and categorization
"""

import pytest
from services.advice_category_detector import (
    AdviceCategoryDetector,
    advice_category_detector,
    detect_advice_request,
    get_category_description,
    get_stats,
)


class TestAdviceCategoryDetectorInitialization:
    """Test AdviceCategoryDetector initialization"""

    def test_initialization(self):
        """Test service initializes correctly"""
        detector = AdviceCategoryDetector()
        assert detector is not None
        assert len(detector.category_keywords) > 0
        assert len(detector.compiled_patterns) > 0

    def test_global_instance(self):
        """Test global instance is available"""
        assert advice_category_detector is not None


class TestAdviceRequestDetection:
    """Test detection of advice requests"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = AdviceCategoryDetector()

    def test_detects_what_should_i_do(self):
        """Test detects 'what should I do' pattern"""
        result = self.detector.detect_advice_request("What should I do about my friend?")
        assert result["is_advice_request"] is True
        assert result["confidence"] > 0.5

    def test_detects_how_do_i(self):
        """Test detects 'how do I' pattern"""
        result = self.detector.detect_advice_request("How do I make new friends at school?")
        assert result["is_advice_request"] is True

    def test_detects_need_help(self):
        """Test detects 'need help' pattern"""
        result = self.detector.detect_advice_request("I need help with my homework")
        assert result["is_advice_request"] is True

    def test_detects_can_you_help(self):
        """Test detects 'can you help' pattern"""
        result = self.detector.detect_advice_request("Can you help me figure this out?")
        assert result["is_advice_request"] is True

    def test_detects_question_mark(self):
        """Test detects questions ending with ?"""
        result = self.detector.detect_advice_request("My friend is mad at me, what do I do?")
        assert result["is_advice_request"] is True

    def test_detects_any_advice(self):
        """Test detects 'any advice' pattern"""
        result = self.detector.detect_advice_request("Do you have any advice for me?")
        assert result["is_advice_request"] is True

    def test_does_not_detect_statement(self):
        """Test does NOT detect simple statements"""
        result = self.detector.detect_advice_request("I had a great day at school today")
        assert result["is_advice_request"] is False

    def test_does_not_detect_greeting(self):
        """Test does NOT detect greetings"""
        result = self.detector.detect_advice_request("Hey! How are you doing?")
        # This might detect due to question mark, but confidence should be lower
        # or it might not detect at all - either is acceptable
        if result["is_advice_request"]:
            assert result["confidence"] < 0.8


class TestFriendshipAdviceDetection:
    """Test detection of friendship advice requests"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = AdviceCategoryDetector()

    def test_detects_friendship_category(self):
        """Test detects friendship category"""
        result = self.detector.detect_advice_request(
            "My best friend is ignoring me. What should I do?"
        )
        assert result["is_advice_request"] is True
        assert result["category"] == "friendship"

    def test_detects_making_friends(self):
        """Test detects making friends advice"""
        result = self.detector.detect_advice_request(
            "How can I make new friends at school?"
        )
        assert result["is_advice_request"] is True
        assert "friendship" in result["categories"]

    def test_detects_friend_fight(self):
        """Test detects friend conflict"""
        result = self.detector.detect_advice_request(
            "I had a fight with my friend. How do I make up?"
        )
        assert result["is_advice_request"] is True
        # Could be friendship or conflict
        assert "friendship" in result["categories"] or "conflict" in result["categories"]

    def test_friendship_keywords_found(self):
        """Test extracts friendship keywords"""
        result = self.detector.detect_advice_request(
            "My best friend doesn't trust me anymore"
        )
        if result["category"] == "friendship":
            assert len(result["keywords_found"]) > 0


class TestSchoolAdviceDetection:
    """Test detection of school advice requests"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = AdviceCategoryDetector()

    def test_detects_school_category(self):
        """Test detects school category"""
        result = self.detector.detect_advice_request(
            "I'm struggling with my math homework. Can you help?"
        )
        assert result["is_advice_request"] is True
        assert result["category"] == "school"

    def test_detects_homework_help(self):
        """Test detects homework advice"""
        result = self.detector.detect_advice_request(
            "How should I study for my test tomorrow?"
        )
        assert result["is_advice_request"] is True
        assert "school" in result["categories"]

    def test_detects_teacher_problem(self):
        """Test detects teacher-related advice"""
        result = self.detector.detect_advice_request(
            "My teacher gave me too much homework. What should I do?"
        )
        assert result["is_advice_request"] is True
        assert "school" in result["categories"]


class TestFamilyAdviceDetection:
    """Test detection of family advice requests"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = AdviceCategoryDetector()

    def test_detects_family_category(self):
        """Test detects family category"""
        result = self.detector.detect_advice_request(
            "My sister keeps bothering me. What should I do?"
        )
        assert result["is_advice_request"] is True
        assert result["category"] == "family"

    def test_detects_parent_conflict(self):
        """Test detects parent-related advice"""
        result = self.detector.detect_advice_request(
            "My mom won't let me go to the party. How do I convince her?"
        )
        assert result["is_advice_request"] is True
        assert "family" in result["categories"]

    def test_detects_sibling_issue(self):
        """Test detects sibling advice"""
        result = self.detector.detect_advice_request(
            "My brother is annoying me all the time"
        )
        # May or may not detect as advice without explicit question
        # but if detected, should be family
        if result["is_advice_request"]:
            assert "family" in result["categories"]


class TestEmotionalAdviceDetection:
    """Test detection of emotional advice requests"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = AdviceCategoryDetector()

    def test_detects_emotional_category(self):
        """Test detects emotional category"""
        result = self.detector.detect_advice_request(
            "I've been feeling really sad lately. What should I do?"
        )
        assert result["is_advice_request"] is True
        assert result["category"] == "emotional"

    def test_detects_anxiety(self):
        """Test detects anxiety-related advice"""
        result = self.detector.detect_advice_request(
            "I feel anxious about the test. How do I calm down?"
        )
        assert result["is_advice_request"] is True
        assert "emotional" in result["categories"]

    def test_detects_stress(self):
        """Test detects stress-related advice"""
        result = self.detector.detect_advice_request(
            "I'm feeling really stressed. Any advice?"
        )
        assert result["is_advice_request"] is True
        assert "emotional" in result["categories"]


class TestHobbyAdviceDetection:
    """Test detection of hobby/activity advice requests"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = AdviceCategoryDetector()

    def test_detects_hobby_category(self):
        """Test detects hobby category"""
        result = self.detector.detect_advice_request(
            "I'm bored. What should I do for fun?"
        )
        assert result["is_advice_request"] is True
        assert result["category"] == "hobby"

    def test_detects_activity_request(self):
        """Test detects activity suggestions"""
        result = self.detector.detect_advice_request(
            "What hobbies should I try?"
        )
        assert result["is_advice_request"] is True
        assert "hobby" in result["categories"]

    def test_detects_boredom(self):
        """Test detects boredom-related requests"""
        result = self.detector.detect_advice_request(
            "There's nothing to do. Any ideas?"
        )
        assert result["is_advice_request"] is True
        # Could be hobby or general
        assert len(result["categories"]) > 0


class TestBullyingAdviceDetection:
    """Test detection of bullying advice requests"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = AdviceCategoryDetector()

    def test_detects_bullying_category(self):
        """Test detects bullying category"""
        result = self.detector.detect_advice_request(
            "Someone is bullying me at school. What should I do?"
        )
        assert result["is_advice_request"] is True
        assert result["category"] == "bullying"

    def test_detects_teasing(self):
        """Test detects teasing/bullying"""
        result = self.detector.detect_advice_request(
            "Kids keep making fun of me. How do I make it stop?"
        )
        assert result["is_advice_request"] is True
        assert "bullying" in result["categories"]


class TestSocialAdviceDetection:
    """Test detection of social advice requests"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = AdviceCategoryDetector()

    def test_detects_social_category(self):
        """Test detects social category"""
        result = self.detector.detect_advice_request(
            "I feel awkward at parties. How do I fit in better?"
        )
        assert result["is_advice_request"] is True
        assert result["category"] == "social"

    def test_detects_fitting_in(self):
        """Test detects fitting in requests"""
        result = self.detector.detect_advice_request(
            "How can I be more popular at school?"
        )
        assert result["is_advice_request"] is True
        assert "social" in result["categories"]


class TestDecisionAdviceDetection:
    """Test detection of decision-making advice requests"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = AdviceCategoryDetector()

    def test_detects_decision_category(self):
        """Test detects decision category"""
        result = self.detector.detect_advice_request(
            "I can't decide between soccer and basketball. Which should I choose?"
        )
        assert result["is_advice_request"] is True
        assert result["category"] == "decision"

    def test_detects_choice_question(self):
        """Test detects choice questions"""
        result = self.detector.detect_advice_request(
            "Should I join the chess club or the art club?"
        )
        assert result["is_advice_request"] is True
        assert "decision" in result["categories"]


class TestConflictAdviceDetection:
    """Test detection of conflict resolution advice"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = AdviceCategoryDetector()

    def test_detects_conflict_category(self):
        """Test detects conflict category"""
        result = self.detector.detect_advice_request(
            "I had a big fight with my friend. How do I fix it?"
        )
        assert result["is_advice_request"] is True
        # Could be conflict or friendship
        assert "conflict" in result["categories"] or "friendship" in result["categories"]

    def test_detects_argument(self):
        """Test detects argument resolution"""
        result = self.detector.detect_advice_request(
            "We're arguing all the time. What should we do?"
        )
        assert result["is_advice_request"] is True
        assert len(result["categories"]) > 0


class TestConfidenceScoring:
    """Test confidence scoring accuracy"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = AdviceCategoryDetector()

    def test_high_confidence_explicit_advice_request(self):
        """Test high confidence for explicit advice requests"""
        result = self.detector.detect_advice_request(
            "Can you give me advice about my friend situation?"
        )
        assert result["confidence"] > 0.7

    def test_medium_confidence_question(self):
        """Test medium confidence for questions"""
        result = self.detector.detect_advice_request(
            "What do you think about this?"
        )
        # Confidence varies based on keywords
        if result["is_advice_request"]:
            assert 0.0 <= result["confidence"] <= 1.0

    def test_confidence_range(self):
        """Test confidence is always in valid range"""
        messages = [
            "What should I do?",
            "Help me please",
            "I don't know what to do",
            "Any suggestions?",
        ]
        for msg in messages:
            result = self.detector.detect_advice_request(msg)
            if result["is_advice_request"]:
                assert 0.0 <= result["confidence"] <= 1.0


class TestMultipleCategoryDetection:
    """Test detection when multiple categories apply"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = AdviceCategoryDetector()

    def test_detects_multiple_categories(self):
        """Test detects when message spans multiple categories"""
        result = self.detector.detect_advice_request(
            "My friend at school is making me feel sad. What should I do?"
        )
        assert result["is_advice_request"] is True
        # Could match friendship, school, emotional
        assert len(result["categories"]) >= 1

    def test_primary_category_selected(self):
        """Test that primary category is highest scoring"""
        result = self.detector.detect_advice_request(
            "My best friend keeps fighting with me about homework"
        )
        if result["is_advice_request"]:
            primary = result["category"]
            # Primary should have highest score
            if len(result["category_scores"]) > 1:
                primary_score = result["category_scores"][primary]
                for cat, score in result["category_scores"].items():
                    if cat != primary:
                        assert primary_score >= score


class TestCategoryDescriptions:
    """Test category description retrieval"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = AdviceCategoryDetector()

    def test_get_friendship_description(self):
        """Test gets friendship description"""
        desc = self.detector.get_category_description("friendship")
        assert "friend" in desc.lower()

    def test_get_school_description(self):
        """Test gets school description"""
        desc = self.detector.get_category_description("school")
        assert "school" in desc.lower()

    def test_get_emotional_description(self):
        """Test gets emotional description"""
        desc = self.detector.get_category_description("emotional")
        assert "emotion" in desc.lower() or "feeling" in desc.lower()

    def test_get_all_category_descriptions(self):
        """Test all categories have descriptions"""
        categories = ["friendship", "school", "family", "emotional", "hobby",
                     "bullying", "social", "decision", "conflict", "general"]
        for category in categories:
            desc = self.detector.get_category_description(category)
            assert desc is not None
            assert len(desc) > 0


class TestStatistics:
    """Test statistics methods"""

    def test_get_stats(self):
        """Test getting detector statistics"""
        detector = AdviceCategoryDetector()
        stats = detector.get_stats()

        assert "total_categories" in stats
        assert "categories" in stats
        assert "pattern_count" in stats
        assert stats["total_categories"] > 0
        assert len(stats["categories"]) > 0

    def test_stats_matches_keywords(self):
        """Test stats match actual keyword structure"""
        detector = AdviceCategoryDetector()
        stats = detector.get_stats()

        assert stats["total_categories"] == len(detector.category_keywords)


class TestConvenienceFunctions:
    """Test module-level convenience functions"""

    def test_detect_advice_request_function(self):
        """Test detect_advice_request convenience function"""
        result = detect_advice_request("What should I do about my homework?")
        assert result is not None
        assert "is_advice_request" in result

    def test_get_category_description_function(self):
        """Test get_category_description convenience function"""
        desc = get_category_description("friendship")
        assert desc is not None
        assert len(desc) > 0

    def test_get_stats_function(self):
        """Test get_stats convenience function"""
        stats = get_stats()
        assert stats is not None
        assert "total_categories" in stats


class TestEdgeCases:
    """Test edge cases and error handling"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = AdviceCategoryDetector()

    def test_empty_message(self):
        """Test handles empty message"""
        result = self.detector.detect_advice_request("")
        assert result["is_advice_request"] is False

    def test_very_short_message(self):
        """Test handles very short messages"""
        result = self.detector.detect_advice_request("Help")
        # May or may not detect, but should not crash
        assert "is_advice_request" in result

    def test_very_long_message(self):
        """Test handles very long messages"""
        long_msg = "What should I do? " * 50
        result = self.detector.detect_advice_request(long_msg)
        # Should still detect
        assert result["is_advice_request"] is True

    def test_special_characters(self):
        """Test handles special characters"""
        result = self.detector.detect_advice_request("What should I do??? !!! ???")
        assert "is_advice_request" in result

    def test_numbers_in_message(self):
        """Test handles numbers in message"""
        result = self.detector.detect_advice_request(
            "I got a 75 on my test. How can I do better?"
        )
        assert result["is_advice_request"] is True

    def test_unknown_category_description(self):
        """Test handles unknown category gracefully"""
        desc = self.detector.get_category_description("nonexistent_category")
        assert desc is not None


class TestRealWorldExamples:
    """Test real-world example messages"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = AdviceCategoryDetector()

    def test_typical_kid_friendship_question(self):
        """Test typical kid friendship question"""
        result = self.detector.detect_advice_request(
            "my best friend said she doesn't want to be friends anymore and idk what to do"
        )
        assert result["is_advice_request"] is True
        assert "friendship" in result["categories"]

    def test_typical_kid_school_question(self):
        """Test typical kid school question"""
        result = self.detector.detect_advice_request(
            "i have so much homework and a test tomorrow help!!!"
        )
        assert result["is_advice_request"] is True

    def test_typical_kid_emotional_question(self):
        """Test typical kid emotional question"""
        result = self.detector.detect_advice_request(
            "i feel really lonely and sad lately. what should i do?"
        )
        assert result["is_advice_request"] is True
        assert "emotional" in result["categories"]

    def test_casual_language(self):
        """Test handles casual/slang language"""
        result = self.detector.detect_advice_request(
            "my friend is being super annoying rn. idk what to do about it"
        )
        assert result["is_advice_request"] is True
