"""
Tests for BullyingKeywordList - Bullying keyword detection service
Tests comprehensive detection of bullying indicators across all categories
"""

import pytest
from services.bullying_keyword_list import BullyingKeywordList, bullying_keyword_list


class TestBullyingKeywordListBasics:
    """Test basic functionality of BullyingKeywordList"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = BullyingKeywordList()

    def test_initialization(self):
        """Test that BullyingKeywordList initializes correctly"""
        assert len(self.detector.physical_bullying_keywords) > 0
        assert len(self.detector.verbal_bullying_keywords) > 0
        assert len(self.detector.social_exclusion_keywords) > 0
        assert len(self.detector.cyberbullying_keywords) > 0
        assert len(self.detector.threat_keywords) > 0
        assert len(self.detector.emotional_impact_keywords) > 0
        assert self.detector.severity == "medium"

    def test_get_stats(self):
        """Test getting keyword statistics"""
        stats = self.detector.get_stats()

        assert "physical_bullying_keywords" in stats
        assert "verbal_bullying_keywords" in stats
        assert "social_exclusion_keywords" in stats
        assert "cyberbullying_keywords" in stats
        assert "threat_keywords" in stats
        assert "emotional_impact_keywords" in stats
        assert "total_keywords" in stats

        # Verify counts are reasonable
        assert stats["physical_bullying_keywords"] >= 10
        assert stats["verbal_bullying_keywords"] >= 10
        assert stats["social_exclusion_keywords"] >= 15
        assert stats["cyberbullying_keywords"] >= 5
        assert stats["threat_keywords"] >= 2
        assert stats["emotional_impact_keywords"] >= 10

        # Verify total is sum of all categories
        assert stats["total_keywords"] == (
            stats["physical_bullying_keywords"]
            + stats["verbal_bullying_keywords"]
            + stats["social_exclusion_keywords"]
            + stats["cyberbullying_keywords"]
            + stats["threat_keywords"]
            + stats["emotional_impact_keywords"]
        )


class TestPhysicalBullyingDetection:
    """Test physical bullying keyword detection"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = BullyingKeywordList()

    def test_general_physical_bullying(self):
        """Test detection of general physical bullying terms"""
        test_cases = [
            "Someone is bullying me at school",
            "I'm getting bullied every day",
            "They keep bullying me",
        ]

        for message in test_cases:
            assert self.detector.contains_bullying_keywords(message)
            assert self.detector.get_category(message) == "physical_bullying"

    def test_pushing_shoving(self):
        """Test detection of pushing/shoving"""
        test_cases = [
            "This kid pushes me around in the hallway",
            "They keep shoving me",
        ]

        for message in test_cases:
            assert self.detector.contains_bullying_keywords(message)
            assert self.detector.get_category(message) == "physical_bullying"

    def test_taking_belongings(self):
        """Test detection of taking belongings"""
        test_cases = [
            "Someone steals my lunch every day",
            "They take my lunch money",
            "He takes my stuff",
        ]

        for message in test_cases:
            assert self.detector.contains_bullying_keywords(message)
            assert self.detector.get_category(message) == "physical_bullying"

    def test_tripping_harassment(self):
        """Test detection of tripping and harassment"""
        test_cases = [
            "Someone trips me in the hallway",
            "They keep tripping me",
            "He knocks my books off the desk",
        ]

        for message in test_cases:
            assert self.detector.contains_bullying_keywords(message)
            assert self.detector.get_category(message) == "physical_bullying"


class TestVerbalBullyingDetection:
    """Test verbal bullying keyword detection"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = BullyingKeywordList()

    def test_name_calling(self):
        """Test detection of name-calling"""
        test_cases = [
            "They call me names all the time",
            "Kids are calling me names",
            "Everyone makes fun of me",
            "They're always making fun of me",
        ]

        for message in test_cases:
            assert self.detector.contains_bullying_keywords(message)
            assert self.detector.get_category(message) == "verbal_bullying"

    def test_teasing(self):
        """Test detection of teasing"""
        test_cases = [
            "Everyone teases me about my clothes",
            "They keep teasing me",
            "Kids are picking on me",
        ]

        for message in test_cases:
            assert self.detector.contains_bullying_keywords(message)
            assert self.detector.get_category(message) == "verbal_bullying"

    def test_mean_comments(self):
        """Test detection of mean comments"""
        test_cases = [
            "They say mean things to me",
            "Kids are saying mean things",
            "People talk about me behind my back",
        ]

        for message in test_cases:
            assert self.detector.contains_bullying_keywords(message)
            assert self.detector.get_category(message) == "verbal_bullying"

    def test_mocking(self):
        """Test detection of mocking"""
        test_cases = [
            "Everyone mocks me when I talk",
            "They keep imitating me to make fun of me",
        ]

        for message in test_cases:
            assert self.detector.contains_bullying_keywords(message)
            assert self.detector.get_category(message) == "verbal_bullying"

    def test_laughing_at(self):
        """Test detection of being laughed at"""
        test_cases = [
            "Everyone laughs at me in class",
            "They're always laughing at me",
        ]

        for message in test_cases:
            assert self.detector.contains_bullying_keywords(message)
            assert self.detector.get_category(message) == "verbal_bullying"


class TestSocialExclusionDetection:
    """Test social exclusion keyword detection"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = BullyingKeywordList()

    def test_direct_exclusion(self):
        """Test detection of direct exclusion"""
        test_cases = [
            "They left me out of the game",
            "Nobody lets me play with them",
            "Everyone excludes me at recess",
        ]

        for message in test_cases:
            assert self.detector.contains_bullying_keywords(message)
            assert self.detector.get_category(message) == "social_exclusion"

    def test_eating_alone(self):
        """Test detection of eating alone"""
        test_cases = [
            "I sit alone at lunch every day",
            "I have to eat lunch alone",
            "I play alone at recess",
        ]

        for message in test_cases:
            assert self.detector.contains_bullying_keywords(message)
            assert self.detector.get_category(message) == "social_exclusion"

    def test_no_friends(self):
        """Test detection of friendship issues"""
        test_cases = [
            "I have no friends at school",
            "Nobody likes me",
            "Everyone hates me",
            "All my friends left me",
        ]

        for message in test_cases:
            assert self.detector.contains_bullying_keywords(message)
            assert self.detector.get_category(message) == "social_exclusion"

    def test_group_exclusion(self):
        """Test detection of group exclusion"""
        test_cases = [
            "They won't sit with me at lunch",
            "Nobody will include me in their group",
            "They shut me out of everything",
        ]

        for message in test_cases:
            assert self.detector.contains_bullying_keywords(message)
            assert self.detector.get_category(message) == "social_exclusion"

    def test_social_isolation(self):
        """Test detection of social isolation"""
        test_cases = [
            "No one talks to me anymore",
            "Nobody talks to me at school",
        ]

        for message in test_cases:
            assert self.detector.contains_bullying_keywords(message)
            assert self.detector.get_category(message) == "social_exclusion"


class TestCyberbullyingDetection:
    """Test cyberbullying keyword detection"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = BullyingKeywordList()

    def test_mean_messages(self):
        """Test detection of mean online messages"""
        test_cases = [
            "Someone sent me mean messages",
            "I keep getting mean texts",
            "People are posting mean comments about me",
        ]

        for message in test_cases:
            assert self.detector.contains_bullying_keywords(message)
            assert self.detector.get_category(message) == "cyberbullying"

    def test_social_media_bullying(self):
        """Test detection of social media bullying"""
        test_cases = [
            "Kids are posting about me on social media",
            "They keep posting lies about me",
        ]

        for message in test_cases:
            assert self.detector.contains_bullying_keywords(message)
            assert self.detector.get_category(message) == "cyberbullying"

    def test_group_chat_exclusion(self):
        """Test detection of group chat exclusion"""
        test_cases = [
            "They made a group chat without me",
            "I got kicked from the group chat",
        ]

        for message in test_cases:
            assert self.detector.contains_bullying_keywords(message)
            assert self.detector.get_category(message) == "cyberbullying"

    def test_online_exclusion(self):
        """Test detection of online exclusion"""
        test_cases = [
            "Everyone unfriended me",
            "They all blocked me",
            "Nobody will add me to their group",
        ]

        for message in test_cases:
            assert self.detector.contains_bullying_keywords(message)
            assert self.detector.get_category(message) == "cyberbullying"


class TestThreatDetection:
    """Test threat keyword detection"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = BullyingKeywordList()

    def test_threat_to_tell(self):
        """Test detection of threats to tell"""
        test_cases = [
            "He threatens to tell everyone my secret",
            "She says she'll tell everyone",
        ]

        for message in test_cases:
            assert self.detector.contains_bullying_keywords(message)
            assert self.detector.get_category(message) == "threats"

    def test_intimidation(self):
        """Test detection of intimidation"""
        test_cases = [
            "This kid intimidates me at school",
            "They scare me at school every day",
        ]

        for message in test_cases:
            assert self.detector.contains_bullying_keywords(message)
            assert self.detector.get_category(message) == "threats"


class TestEmotionalImpactDetection:
    """Test emotional impact keyword detection"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = BullyingKeywordList()

    def test_fear_of_school(self):
        """Test detection of fear of school"""
        test_cases = [
            "I'm scared to go to school",
            "I don't want to go to school anymore",
            "I'm afraid to go to school",
        ]

        for message in test_cases:
            assert self.detector.contains_bullying_keywords(message)
            assert self.detector.get_category(message) == "emotional_impact"

    def test_loneliness(self):
        """Test detection of loneliness"""
        test_cases = [
            "I feel so alone at school",
            "I'm so lonely at school",
        ]

        for message in test_cases:
            assert self.detector.contains_bullying_keywords(message)
            assert self.detector.get_category(message) == "emotional_impact"

    def test_social_anxiety(self):
        """Test detection of social anxiety"""
        test_cases = [
            "Everyone's against me",
            "The whole class hates me",
        ]

        for message in test_cases:
            assert self.detector.contains_bullying_keywords(message)
            assert self.detector.get_category(message) == "emotional_impact"

    def test_rumor_spreading(self):
        """Test detection of rumor spreading"""
        test_cases = [
            "They're spreading rumors about me",
            "Someone told everyone a lie about me",
            "Kids are spreading lies about me",
        ]

        for message in test_cases:
            assert self.detector.contains_bullying_keywords(message)
            assert self.detector.get_category(message) == "emotional_impact"


class TestFindBullyingKeywords:
    """Test finding bullying keywords with details"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = BullyingKeywordList()

    def test_find_physical_keywords(self):
        """Test finding physical bullying keywords with details"""
        message = "Someone is bullying me and pushing me around"
        keywords = self.detector.find_bullying_keywords(message)

        assert len(keywords) > 0
        # Should find at least "bullying me" and "pushing me around"
        assert len(keywords) >= 2

        for kw in keywords:
            assert "keyword" in kw
            assert "category" in kw
            assert "severity" in kw
            assert kw["category"] == "physical_bullying"
            assert kw["severity"] == "medium"

    def test_find_verbal_keywords(self):
        """Test finding verbal bullying keywords with details"""
        message = "Kids call me names and make fun of me every day"
        keywords = self.detector.find_bullying_keywords(message)

        assert len(keywords) > 0
        for kw in keywords:
            assert kw["category"] == "verbal_bullying"
            assert kw["severity"] == "medium"

    def test_find_multiple_categories(self):
        """Test finding keywords from multiple categories"""
        message = "They call me names, left me out of the group, and sent mean messages"
        keywords = self.detector.find_bullying_keywords(message)

        assert len(keywords) >= 3
        categories = set(kw["category"] for kw in keywords)
        # Should detect verbal, social, and cyber
        assert "verbal_bullying" in categories
        assert "social_exclusion" in categories
        assert "cyberbullying" in categories


class TestGetAllCategories:
    """Test getting all bullying categories detected"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = BullyingKeywordList()

    def test_single_category(self):
        """Test detection of single category"""
        message = "They call me names"
        categories = self.detector.get_all_categories(message)

        assert len(categories) == 1
        assert "verbal_bullying" in categories

    def test_multiple_categories(self):
        """Test detection of multiple categories"""
        message = "They call me names and left me out of the game"
        categories = self.detector.get_all_categories(message)

        assert len(categories) == 2
        assert "verbal_bullying" in categories
        assert "social_exclusion" in categories

    def test_all_categories(self):
        """Test detection of all bullying types"""
        message = "They bully me, call me names, left me out, sent mean messages, threaten me, and I'm scared to go to school"
        categories = self.detector.get_all_categories(message)

        # Should detect all 6 categories
        assert len(categories) == 6
        assert "physical_bullying" in categories
        assert "verbal_bullying" in categories
        assert "social_exclusion" in categories
        assert "cyberbullying" in categories
        assert "threats" in categories
        assert "emotional_impact" in categories


class TestCategoryPriority:
    """Test category priority in get_category method"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = BullyingKeywordList()

    def test_threats_priority(self):
        """Test that threats have highest priority"""
        message = "They bully me and threaten to tell everyone"
        category = self.detector.get_category(message)

        # Threats should be returned as primary category
        assert category == "threats"

    def test_physical_priority_over_verbal(self):
        """Test that physical bullying has priority over verbal"""
        message = "They call me names and push me around"
        category = self.detector.get_category(message)

        # Physical should be returned as primary category
        assert category == "physical_bullying"

    def test_cyber_priority_over_verbal(self):
        """Test that cyberbullying has priority over verbal"""
        message = "They call me names and send mean messages"
        category = self.detector.get_category(message)

        # Cyberbullying should be returned
        assert category == "cyberbullying"


class TestSafeMessages:
    """Test that safe messages are not flagged"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = BullyingKeywordList()

    def test_safe_conversation(self):
        """Test that safe messages return no bullying"""
        safe_messages = [
            "Can you help me with my homework?",
            "I had a great day at school today",
            "What's your favorite subject?",
            "I love playing chess with my friends",
            "How do I solve this math problem?",
        ]

        for message in safe_messages:
            assert not self.detector.contains_bullying_keywords(message)
            assert self.detector.get_category(message) == "none"
            assert len(self.detector.find_bullying_keywords(message)) == 0


class TestCaseInsensitivity:
    """Test case insensitive detection"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = BullyingKeywordList()

    def test_uppercase(self):
        """Test detection works with uppercase"""
        message = "THEY'RE BULLYING ME"
        assert self.detector.contains_bullying_keywords(message)
        assert self.detector.get_category(message) == "physical_bullying"

    def test_mixed_case(self):
        """Test detection works with mixed case"""
        message = "ThEy CaLl Me NaMeS"
        assert self.detector.contains_bullying_keywords(message)
        assert self.detector.get_category(message) == "verbal_bullying"

    def test_lowercase(self):
        """Test detection works with lowercase"""
        message = "everyone left me out"
        assert self.detector.contains_bullying_keywords(message)
        assert self.detector.get_category(message) == "social_exclusion"


class TestConvenienceFunctions:
    """Test module-level convenience functions"""

    def test_contains_bullying_keywords_function(self):
        """Test convenience function for contains check"""
        from services.bullying_keyword_list import contains_bullying_keywords

        assert contains_bullying_keywords("They're bullying me")
        assert not contains_bullying_keywords("Hello, how are you?")

    def test_find_bullying_keywords_function(self):
        """Test convenience function for finding keywords"""
        from services.bullying_keyword_list import find_bullying_keywords

        keywords = find_bullying_keywords("They call me names")
        assert len(keywords) > 0

    def test_get_category_function(self):
        """Test convenience function for getting category"""
        from services.bullying_keyword_list import get_category

        assert get_category("They're bullying me") == "physical_bullying"
        assert get_category("They call me names") == "verbal_bullying"
        assert get_category("Hello") == "none"

    def test_get_all_categories_function(self):
        """Test convenience function for getting all categories"""
        from services.bullying_keyword_list import get_all_categories

        categories = get_all_categories("They bully me and call me names")
        assert "physical_bullying" in categories
        assert "verbal_bullying" in categories

    def test_get_stats_function(self):
        """Test convenience function for getting stats"""
        from services.bullying_keyword_list import get_stats

        stats = get_stats()
        assert "total_keywords" in stats
        assert stats["total_keywords"] > 0


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = BullyingKeywordList()

    def test_empty_string(self):
        """Test empty string handling"""
        assert not self.detector.contains_bullying_keywords("")
        assert self.detector.get_category("") == "none"
        assert len(self.detector.find_bullying_keywords("")) == 0

    def test_whitespace_only(self):
        """Test whitespace-only string"""
        assert not self.detector.contains_bullying_keywords("   \n\t  ")
        assert self.detector.get_category("   \n\t  ") == "none"

    def test_very_long_message(self):
        """Test very long message with bullying keyword"""
        long_message = "This is a long message. " * 100 + "They're bullying me"
        assert self.detector.contains_bullying_keywords(long_message)
        assert self.detector.get_category(long_message) == "physical_bullying"

    def test_keyword_in_context(self):
        """Test keyword detected even in complex context"""
        message = "I've been trying to deal with it myself but they keep calling me names and it really hurts"
        assert self.detector.contains_bullying_keywords(message)
        assert self.detector.get_category(message) == "verbal_bullying"


class TestRealWorldScenarios:
    """Test realistic bullying scenarios"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = BullyingKeywordList()

    def test_school_lunch_exclusion(self):
        """Test realistic lunch exclusion scenario"""
        message = "I sit alone at lunch every day and nobody talks to me"
        assert self.detector.contains_bullying_keywords(message)
        categories = self.detector.get_all_categories(message)
        assert "social_exclusion" in categories

    def test_recess_bullying(self):
        """Test realistic recess bullying scenario"""
        message = "Kids push me around at recess and won't let me play with them"
        assert self.detector.contains_bullying_keywords(message)
        categories = self.detector.get_all_categories(message)
        assert "physical_bullying" in categories
        assert "social_exclusion" in categories

    def test_online_bullying_scenario(self):
        """Test realistic online bullying scenario"""
        message = "Everyone in my class is in a group chat but they left me out and they're posting mean comments"
        assert self.detector.contains_bullying_keywords(message)
        categories = self.detector.get_all_categories(message)
        assert "cyberbullying" in categories

    def test_combined_bullying(self):
        """Test realistic combined bullying scenario"""
        message = "Kids at school make fun of me, left me out of their group, and now they're posting about me online"
        assert self.detector.contains_bullying_keywords(message)
        categories = self.detector.get_all_categories(message)
        assert len(categories) >= 2
        assert "verbal_bullying" in categories
        assert "social_exclusion" in categories
        assert "cyberbullying" in categories

    def test_emotional_distress(self):
        """Test realistic emotional distress from bullying"""
        message = "I'm scared to go to school because everyone hates me"
        assert self.detector.contains_bullying_keywords(message)
        categories = self.detector.get_all_categories(message)
        assert "emotional_impact" in categories
        assert "social_exclusion" in categories


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
