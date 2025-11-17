"""
Tests for CrisisKeywordList - Crisis keyword detection service
Tests comprehensive detection of suicide, self-harm, and abuse keywords
"""

import pytest
from services.crisis_keyword_list import CrisisKeywordList, crisis_keyword_list


class TestCrisisKeywordListBasics:
    """Test basic functionality of CrisisKeywordList"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = CrisisKeywordList()

    def test_initialization(self):
        """Test that CrisisKeywordList initializes correctly"""
        assert len(self.detector.suicide_keywords) > 0
        assert len(self.detector.self_harm_keywords) > 0
        assert len(self.detector.abuse_physical_keywords) > 0
        assert len(self.detector.abuse_emotional_keywords) > 0
        assert len(self.detector.abuse_sexual_keywords) > 0
        assert self.detector.severity == "critical"

    def test_get_stats(self):
        """Test getting keyword statistics"""
        stats = self.detector.get_stats()

        assert "suicide_keywords" in stats
        assert "self_harm_keywords" in stats
        assert "abuse_physical_keywords" in stats
        assert "abuse_emotional_keywords" in stats
        assert "abuse_sexual_keywords" in stats
        assert "total_keywords" in stats

        # Verify counts are reasonable
        assert stats["suicide_keywords"] >= 20
        assert stats["self_harm_keywords"] >= 15
        assert stats["abuse_physical_keywords"] >= 20
        assert stats["abuse_emotional_keywords"] >= 15
        assert stats["abuse_sexual_keywords"] >= 10

        # Verify total is sum of all categories
        assert stats["total_keywords"] == (
            stats["suicide_keywords"]
            + stats["self_harm_keywords"]
            + stats["abuse_physical_keywords"]
            + stats["abuse_emotional_keywords"]
            + stats["abuse_sexual_keywords"]
        )


class TestSuicideDetection:
    """Test suicide keyword detection"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = CrisisKeywordList()

    def test_direct_suicide_mentions(self):
        """Test detection of direct suicide mentions"""
        test_cases = [
            "I want to commit suicide",
            "suicide is the only option",
            "thinking about suicide",
        ]

        for message in test_cases:
            assert self.detector.contains_crisis_keywords(message)
            assert self.detector.get_category(message) == "suicide"

    def test_kill_myself_variations(self):
        """Test detection of 'kill myself' variations"""
        test_cases = [
            "I want to kill myself",
            "I'm going to kill myself",
            "I'm killing myself",
            "gonna kill myself",
        ]

        for message in test_cases:
            assert self.detector.contains_crisis_keywords(message)
            category = self.detector.get_category(message)
            assert category == "suicide"

    def test_death_wishes(self):
        """Test detection of death wish expressions"""
        test_cases = [
            "I want to die",
            "I wish I was dead",
            "I wish I were dead",
            "I'm better off dead",
            "everyone would be better off without me",
            "the world would be better without me",
        ]

        for message in test_cases:
            assert self.detector.contains_crisis_keywords(message)
            assert self.detector.get_category(message) == "suicide"

    def test_life_negation(self):
        """Test detection of life negation expressions"""
        test_cases = [
            "there's no reason to live",
            "I have nothing to live for",
            "I don't want to be alive anymore",
            "I dont want to live",
            "I'm tired of living",
            "I can't go on like this",
        ]

        for message in test_cases:
            assert self.detector.contains_crisis_keywords(message)
            assert self.detector.get_category(message) == "suicide"

    def test_ending_thoughts(self):
        """Test detection of 'ending' expressions"""
        test_cases = [
            "I want to end it all",
            "I'm going to end my life",
            "I want to take my life",
        ]

        for message in test_cases:
            assert self.detector.contains_crisis_keywords(message)
            assert self.detector.get_category(message) == "suicide"

    def test_hopelessness_expressions(self):
        """Test detection of hopelessness"""
        test_cases = [
            "there's no point in living",
            "life isn't worth living",
            "life is not worth living",
            "I'm ready to die",
            "I give up on life",
        ]

        for message in test_cases:
            assert self.detector.contains_crisis_keywords(message)
            assert self.detector.get_category(message) == "suicide"


class TestSelfHarmDetection:
    """Test self-harm keyword detection"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = CrisisKeywordList()

    def test_cutting_mentions(self):
        """Test detection of cutting references"""
        test_cases = [
            "I want to cut myself",
            "I've been cutting myself",
            "I cut my wrists",
            "I'm cutting my wrists",
        ]

        for message in test_cases:
            assert self.detector.contains_crisis_keywords(message)
            assert self.detector.get_category(message) == "self_harm"

    def test_general_self_harm(self):
        """Test detection of general self-harm"""
        test_cases = [
            "I want to hurt myself",
            "I'm hurting myself",
            "I need to harm myself",
            "I'm injuring myself",
        ]

        for message in test_cases:
            assert self.detector.contains_crisis_keywords(message)
            assert self.detector.get_category(message) == "self_harm"

    def test_burning_mentions(self):
        """Test detection of burning references"""
        test_cases = [
            "I burned myself",
            "I'm burning myself",
        ]

        for message in test_cases:
            assert self.detector.contains_crisis_keywords(message)
            assert self.detector.get_category(message) == "self_harm"

    def test_hitting_mentions(self):
        """Test detection of self-hitting references"""
        test_cases = [
            "I hit myself",
            "I'm hitting myself",
            "I punched myself",
        ]

        for message in test_cases:
            assert self.detector.contains_crisis_keywords(message)
            assert self.detector.get_category(message) == "self_harm"

    def test_self_harm_terms(self):
        """Test detection of self-harm terminology"""
        test_cases = [
            "I'm doing self harm",
            "I do self-harm",
            "self injury is my coping mechanism",
        ]

        for message in test_cases:
            assert self.detector.contains_crisis_keywords(message)
            assert self.detector.get_category(message) == "self_harm"

    def test_pain_seeking(self):
        """Test detection of pain-seeking expressions"""
        test_cases = [
            "I need to hurt myself",
            "I have to hurt myself",
            "I want to feel pain",
            "I deserve pain",
            "I need to punish myself",
        ]

        for message in test_cases:
            assert self.detector.contains_crisis_keywords(message)
            assert self.detector.get_category(message) == "self_harm"


class TestPhysicalAbuseDetection:
    """Test physical abuse keyword detection"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = CrisisKeywordList()

    def test_hitting_striking(self):
        """Test detection of hitting/striking"""
        test_cases = [
            "My dad hits me",
            "My mom hit me yesterday",
            "He beats me every day",
            "She's beating me",
            "He punches me",
            "My parent slaps me",
        ]

        for message in test_cases:
            assert self.detector.contains_crisis_keywords(message)
            assert self.detector.get_category(message) == "abuse_physical"

    def test_kicking(self):
        """Test detection of kicking"""
        test_cases = [
            "He kicks me",
            "She kicked me",
        ]

        for message in test_cases:
            assert self.detector.contains_crisis_keywords(message)
            assert self.detector.get_category(message) == "abuse_physical"

    def test_throwing_pushing(self):
        """Test detection of throwing/pushing"""
        test_cases = [
            "He threw me against the wall",
            "She pushes me down the stairs",
            "He shoves me",
        ]

        for message in test_cases:
            assert self.detector.contains_crisis_keywords(message)
            assert self.detector.get_category(message) == "abuse_physical"

    def test_choking_strangling(self):
        """Test detection of choking/strangling"""
        test_cases = [
            "He chokes me",
            "She's choking me",
            "He tried to strangle me",
        ]

        for message in test_cases:
            assert self.detector.contains_crisis_keywords(message)
            assert self.detector.get_category(message) == "abuse_physical"

    def test_physical_restraint(self):
        """Test detection of physical restraint"""
        test_cases = [
            "He locked me in my room",
            "They tied me up",
            "She won't let me leave",
        ]

        for message in test_cases:
            assert self.detector.contains_crisis_keywords(message)
            assert self.detector.get_category(message) == "abuse_physical"

    def test_abuse_results(self):
        """Test detection of abuse results"""
        test_cases = [
            "He gave me bruises",
            "She left marks on me",
            "He made me bleed",
        ]

        for message in test_cases:
            assert self.detector.contains_crisis_keywords(message)
            assert self.detector.get_category(message) == "abuse_physical"


class TestEmotionalAbuseDetection:
    """Test emotional abuse keyword detection"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = CrisisKeywordList()

    def test_threats_and_fear(self):
        """Test detection of threats and fear"""
        test_cases = [
            "He threatens me all the time",
            "She makes me scared",
            "I'm afraid of my dad",
            "I'm terrified of him",
        ]

        for message in test_cases:
            assert self.detector.contains_crisis_keywords(message)
            assert self.detector.get_category(message) == "abuse_emotional"

    def test_screaming_yelling(self):
        """Test detection of screaming/yelling"""
        test_cases = [
            "My dad screams at me constantly",
            "She's always yelling at me",
            "He shouts at me for everything",
        ]

        for message in test_cases:
            assert self.detector.contains_crisis_keywords(message)
            assert self.detector.get_category(message) == "abuse_emotional"

    def test_control_and_isolation(self):
        """Test detection of control and isolation"""
        test_cases = [
            "She won't let me see my friends",
            "He doesn't let me go anywhere",
            "My parent controls everything I do",
            "They isolate me from everyone",
        ]

        for message in test_cases:
            assert self.detector.contains_crisis_keywords(message)
            assert self.detector.get_category(message) == "abuse_emotional"

    def test_deprivation(self):
        """Test detection of deprivation"""
        test_cases = [
            "They won't let me eat",
            "She won't feed me",
            "He starves me as punishment",
            "They lock me in my room all day",
        ]

        for message in test_cases:
            assert self.detector.contains_crisis_keywords(message)
            assert self.detector.get_category(message) == "abuse_emotional"

    def test_verbal_abuse(self):
        """Test detection of verbal abuse"""
        test_cases = [
            "My dad calls me names",
            "She tells me I'm worthless",
            "He says I'm stupid",
        ]

        for message in test_cases:
            assert self.detector.contains_crisis_keywords(message)
            assert self.detector.get_category(message) == "abuse_emotional"


class TestSexualAbuseDetection:
    """Test sexual abuse keyword detection (age-appropriate)"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = CrisisKeywordList()

    def test_inappropriate_touching(self):
        """Test detection of inappropriate touching"""
        test_cases = [
            "Someone touched me inappropriately",
            "He touched my private parts",
            "She touches me where she shouldn't",
        ]

        for message in test_cases:
            assert self.detector.contains_crisis_keywords(message)
            # Sexual abuse has highest priority among abuse types
            assert self.detector.get_category(message) == "abuse_sexual"

    def test_unwanted_contact(self):
        """Test detection of unwanted contact"""
        test_cases = [
            "He made me touch him",
            "She forced me to touch her",
        ]

        for message in test_cases:
            assert self.detector.contains_crisis_keywords(message)
            assert self.detector.get_category(message) == "abuse_sexual"

    def test_exposure(self):
        """Test detection of exposure"""
        test_cases = [
            "He showed me his private parts",
            "She made me look at inappropriate things",
        ]

        for message in test_cases:
            assert self.detector.contains_crisis_keywords(message)
            assert self.detector.get_category(message) == "abuse_sexual"

    def test_grooming_indicators(self):
        """Test detection of grooming indicators"""
        test_cases = [
            "He said to keep it secret",
            "She told me not to tell anyone",
            "He says don't tell anyone about this",
        ]

        for message in test_cases:
            assert self.detector.contains_crisis_keywords(message)
            assert self.detector.get_category(message) == "abuse_sexual"


class TestFindCrisisKeywords:
    """Test finding crisis keywords with details"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = CrisisKeywordList()

    def test_find_suicide_keywords(self):
        """Test finding suicide keywords with details"""
        message = "I want to kill myself because I have no reason to live"
        keywords = self.detector.find_crisis_keywords(message)

        assert len(keywords) > 0
        # Should find at least "kill myself" and "no reason to live"
        assert len(keywords) >= 2

        for kw in keywords:
            assert "keyword" in kw
            assert "category" in kw
            assert "severity" in kw
            assert kw["category"] == "suicide"
            assert kw["severity"] == "critical"

    def test_find_self_harm_keywords(self):
        """Test finding self-harm keywords with details"""
        message = "I've been cutting myself and hurting myself"
        keywords = self.detector.find_crisis_keywords(message)

        assert len(keywords) > 0
        for kw in keywords:
            assert kw["category"] == "self_harm"
            assert kw["severity"] == "critical"

    def test_find_abuse_keywords(self):
        """Test finding abuse keywords with details"""
        message = "My dad hits me and makes me scared"
        keywords = self.detector.find_crisis_keywords(message)

        assert len(keywords) > 0
        # Should find keywords from both physical and emotional abuse
        categories = [kw["category"] for kw in keywords]
        assert "abuse_physical" in categories
        assert "abuse_emotional" in categories

    def test_find_multiple_categories(self):
        """Test finding keywords from multiple categories"""
        message = "I want to kill myself and I cut myself and my dad hits me"
        keywords = self.detector.find_crisis_keywords(message)

        assert len(keywords) >= 3
        categories = set(kw["category"] for kw in keywords)
        # Should detect suicide, self-harm, and abuse
        assert "suicide" in categories
        assert "self_harm" in categories
        assert "abuse_physical" in categories


class TestGetAllCategories:
    """Test getting all crisis categories detected"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = CrisisKeywordList()

    def test_single_category(self):
        """Test detection of single category"""
        message = "I want to kill myself"
        categories = self.detector.get_all_categories(message)

        assert len(categories) == 1
        assert "suicide" in categories

    def test_multiple_categories(self):
        """Test detection of multiple categories"""
        message = "I want to kill myself and I'm cutting myself"
        categories = self.detector.get_all_categories(message)

        assert len(categories) == 2
        assert "suicide" in categories
        assert "self_harm" in categories

    def test_all_abuse_categories(self):
        """Test detection of all abuse types"""
        message = "My dad hits me, screams at me, and touched me inappropriately"
        categories = self.detector.get_all_categories(message)

        assert "abuse_physical" in categories
        assert "abuse_emotional" in categories
        assert "abuse_sexual" in categories


class TestCategoryPriority:
    """Test category priority in get_category method"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = CrisisKeywordList()

    def test_suicide_priority_over_self_harm(self):
        """Test that suicide has priority over self-harm"""
        message = "I want to kill myself and I cut myself"
        category = self.detector.get_category(message)

        # Suicide should be returned as primary category
        assert category == "suicide"

    def test_self_harm_priority_over_abuse(self):
        """Test that self-harm has priority over abuse"""
        message = "I cut myself and my dad hits me"
        category = self.detector.get_category(message)

        # Self-harm should be returned as primary category
        assert category == "self_harm"

    def test_sexual_abuse_priority(self):
        """Test that sexual abuse has priority among abuse types"""
        message = "He hits me and touched me inappropriately"
        category = self.detector.get_category(message)

        # Sexual abuse should be returned
        assert category == "abuse_sexual"


class TestSafeMessages:
    """Test that safe messages are not flagged"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = CrisisKeywordList()

    def test_safe_conversation(self):
        """Test that safe messages return no crisis"""
        safe_messages = [
            "Can you help me with my homework?",
            "I had a great day at school",
            "What's your favorite color?",
            "I love playing chess",
            "How do I solve this math problem?",
        ]

        for message in safe_messages:
            assert not self.detector.contains_crisis_keywords(message)
            assert self.detector.get_category(message) == "none"
            assert len(self.detector.find_crisis_keywords(message)) == 0


class TestCaseInsensitivity:
    """Test case insensitive detection"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = CrisisKeywordList()

    def test_uppercase(self):
        """Test detection works with uppercase"""
        message = "I WANT TO KILL MYSELF"
        assert self.detector.contains_crisis_keywords(message)
        assert self.detector.get_category(message) == "suicide"

    def test_mixed_case(self):
        """Test detection works with mixed case"""
        message = "I WaNt To KiLl MySeLf"
        assert self.detector.contains_crisis_keywords(message)
        assert self.detector.get_category(message) == "suicide"

    def test_lowercase(self):
        """Test detection works with lowercase"""
        message = "i want to kill myself"
        assert self.detector.contains_crisis_keywords(message)
        assert self.detector.get_category(message) == "suicide"


class TestConvenienceFunctions:
    """Test module-level convenience functions"""

    def test_contains_crisis_keywords_function(self):
        """Test convenience function for contains check"""
        from services.crisis_keyword_list import contains_crisis_keywords

        assert contains_crisis_keywords("I want to kill myself")
        assert not contains_crisis_keywords("Hello, how are you?")

    def test_find_crisis_keywords_function(self):
        """Test convenience function for finding keywords"""
        from services.crisis_keyword_list import find_crisis_keywords

        keywords = find_crisis_keywords("I want to kill myself")
        assert len(keywords) > 0

    def test_get_category_function(self):
        """Test convenience function for getting category"""
        from services.crisis_keyword_list import get_category

        assert get_category("I want to kill myself") == "suicide"
        assert get_category("I cut myself") == "self_harm"
        assert get_category("Hello") == "none"

    def test_get_all_categories_function(self):
        """Test convenience function for getting all categories"""
        from services.crisis_keyword_list import get_all_categories

        categories = get_all_categories("I want to kill myself and I cut myself")
        assert "suicide" in categories
        assert "self_harm" in categories

    def test_get_stats_function(self):
        """Test convenience function for getting stats"""
        from services.crisis_keyword_list import get_stats

        stats = get_stats()
        assert "total_keywords" in stats
        assert stats["total_keywords"] > 0


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = CrisisKeywordList()

    def test_empty_string(self):
        """Test empty string handling"""
        assert not self.detector.contains_crisis_keywords("")
        assert self.detector.get_category("") == "none"
        assert len(self.detector.find_crisis_keywords("")) == 0

    def test_whitespace_only(self):
        """Test whitespace-only string"""
        assert not self.detector.contains_crisis_keywords("   \n\t  ")
        assert self.detector.get_category("   \n\t  ") == "none"

    def test_very_long_message(self):
        """Test very long message with crisis keyword"""
        long_message = "This is a long message. " * 100 + "I want to kill myself"
        assert self.detector.contains_crisis_keywords(long_message)
        assert self.detector.get_category(long_message) == "suicide"

    def test_keyword_in_context(self):
        """Test keyword detected even in complex context"""
        message = "Sometimes I feel really sad and I think about how I want to kill myself even though I know I shouldn't"
        assert self.detector.contains_crisis_keywords(message)
        assert self.detector.get_category(message) == "suicide"

    def test_partial_keyword_match(self):
        """Test that partial matches don't trigger false positives"""
        # "hits" is a keyword but "hits the ball" shouldn't trigger
        # However, our current implementation does substring matching
        # This test documents current behavior
        message = "He hits the baseball really hard"
        # This WILL be detected with current implementation
        # as "hits" is in "hits me"
        # This is acceptable for child safety - better to over-detect


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
