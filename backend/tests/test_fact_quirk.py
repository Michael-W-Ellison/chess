"""
Tests for Fact Quirk Service
Task 71: Implement shares_facts quirk
"""

import pytest
from services.fact_quirk_service import FactQuirkService, fact_quirk_service


class TestFactQuirkService:
    """Test fact quirk service initialization and basic functionality"""

    def test_service_initialization(self):
        """Test that service initializes correctly"""
        service = FactQuirkService()
        assert service is not None
        assert hasattr(service, 'SCIENCE_FACTS')
        assert hasattr(service, 'ANIMAL_FACTS')
        assert hasattr(service, 'CONTEXT_KEYWORDS')

    def test_global_instance_exists(self):
        """Test that global singleton instance exists"""
        assert fact_quirk_service is not None

    def test_fact_collections_not_empty(self):
        """Test that fact collections are populated"""
        service = FactQuirkService()
        assert len(service.SCIENCE_FACTS) > 0
        assert len(service.ANIMAL_FACTS) > 0
        assert len(service.SPACE_FACTS) > 0
        assert len(service.NATURE_FACTS) > 0
        assert len(service.HISTORY_FACTS) > 0
        assert len(service.TECH_FACTS) > 0


class TestFactAddition:
    """Test adding facts to responses"""

    def test_add_fact_with_high_probability(self):
        """Test fact addition with high probability"""
        service = FactQuirkService()
        response = "That's interesting!"
        result = service.add_fact(response, context="", probability=1.0)

        # With probability=1.0, fact should always be added
        assert len(result) > len(response)
        assert "That's interesting!" in result
        assert "Did you know?" in result

    def test_add_fact_with_zero_probability(self):
        """Test that no fact is added with zero probability"""
        service = FactQuirkService()
        response = "That's interesting!"
        result = service.add_fact(response, context="", probability=0.0)

        # With probability=0.0, no fact should be added
        assert result == response

    def test_add_fact_preserves_original_response(self):
        """Test that original response is preserved"""
        service = FactQuirkService()
        response = "I can help you with that."
        result = service.add_fact(response, context="", probability=1.0)

        # Original response should still be in result
        assert "help you with that" in result

    def test_add_fact_to_empty_response(self):
        """Test adding fact to empty response"""
        service = FactQuirkService()
        response = ""
        result = service.add_fact(response, context="", probability=1.0)

        # Should just return a fact
        assert len(result) > 0
        assert "Did you know?" in result


class TestContextualFacts:
    """Test context-based fact selection"""

    def test_science_context_fact(self):
        """Test fact for science-related context"""
        service = FactQuirkService()
        context = "I love science experiments"
        result = service.add_fact("Cool!", context=context, probability=1.0)

        # Should add a fact (science-related preferred)
        assert len(result) > len("Cool!")
        assert "Did you know?" in result

    def test_animal_context_fact(self):
        """Test fact for animal-related context"""
        service = FactQuirkService()
        context = "I have a pet dog"
        result = service.add_fact("Nice!", context=context, probability=1.0)

        assert "Nice!" in result
        assert len(result) > len("Nice!")

    def test_space_context_fact(self):
        """Test fact for space-related context"""
        service = FactQuirkService()
        context = "I love learning about planets"
        result = service.add_fact("Awesome!", context=context, probability=1.0)

        assert "Awesome!" in result

    def test_nature_context_fact(self):
        """Test fact for nature-related context"""
        service = FactQuirkService()
        context = "Trees are beautiful"
        result = service.add_fact("Agreed!", context=context, probability=1.0)

        assert "Agreed!" in result

    def test_no_context_uses_general_fact(self):
        """Test that general facts are used without context"""
        service = FactQuirkService()
        result = service.add_fact("Cool!", context="", probability=1.0)

        # Should add a general fact
        assert len(result) > len("Cool!")
        assert "Did you know?" in result


class TestGetContextualFact:
    """Test contextual fact retrieval"""

    def test_get_contextual_fact_science(self):
        """Test getting science-related fact"""
        service = FactQuirkService()
        fact = service._get_contextual_fact("I have a science test")

        # Should return a fact (likely science-related)
        assert fact is not None
        assert isinstance(fact, str)
        assert len(fact) > 0
        assert "Did you know?" in fact

    def test_get_contextual_fact_no_match(self):
        """Test getting fact with no keyword match"""
        service = FactQuirkService()
        fact = service._get_contextual_fact("xyz abc def")

        # Should return None when no match
        assert fact is None

    def test_get_contextual_fact_empty_context(self):
        """Test getting fact with empty context"""
        service = FactQuirkService()
        fact = service._get_contextual_fact("")

        # Should return None for empty context
        assert fact is None


class TestGetRandomFact:
    """Test random fact selection"""

    def test_get_random_fact_returns_string(self):
        """Test that random fact returns a string"""
        service = FactQuirkService()
        fact = service._get_random_fact()

        assert isinstance(fact, str)
        assert len(fact) > 0
        assert "Did you know?" in fact

    def test_get_random_fact_different_calls(self):
        """Test that random fact can return different results"""
        service = FactQuirkService()

        # Get multiple facts
        facts = [service._get_random_fact() for _ in range(10)]

        # At least some should be different (probabilistic test)
        assert len(set(facts)) > 1


class TestGetFactByCategory:
    """Test getting facts by specific category"""

    def test_get_fact_by_category_science(self):
        """Test getting science fact"""
        service = FactQuirkService()
        fact = service.get_fact_by_category("science")

        assert isinstance(fact, str)
        assert fact in service.SCIENCE_FACTS

    def test_get_fact_by_category_animal(self):
        """Test getting animal fact"""
        service = FactQuirkService()
        fact = service.get_fact_by_category("animal")

        assert fact in service.ANIMAL_FACTS

    def test_get_fact_by_category_space(self):
        """Test getting space fact"""
        service = FactQuirkService()
        fact = service.get_fact_by_category("space")

        assert fact in service.SPACE_FACTS

    def test_get_fact_by_category_nature(self):
        """Test getting nature fact"""
        service = FactQuirkService()
        fact = service.get_fact_by_category("nature")

        assert fact in service.NATURE_FACTS

    def test_get_fact_by_category_history(self):
        """Test getting history fact"""
        service = FactQuirkService()
        fact = service.get_fact_by_category("history")

        assert fact in service.HISTORY_FACTS

    def test_get_fact_by_category_invalid(self):
        """Test getting fact with invalid category falls back to general"""
        service = FactQuirkService()
        fact = service.get_fact_by_category("invalid_category")

        # Should fall back to general facts
        assert fact in service.GENERAL_FACTS


class TestFactTransitions:
    """Test fact transition phrases"""

    def test_fact_has_transition_sometimes(self):
        """Test that facts sometimes include transition phrases"""
        service = FactQuirkService()

        # Get multiple facts to test probabilistic transitions
        results = []
        for _ in range(20):
            result = service.add_fact("Hello", context="", probability=1.0)
            results.append(result)

        # Check if any have transition phrases
        has_transitions = any(
            "Here's something cool" in r or
            "Fun fact" in r or
            "By the way" in r or
            "Also" in r
            for r in results
        )

        # At least some should have transitions (probabilistic)
        assert has_transitions


class TestFactContent:
    """Test that facts are educational and well-formed"""

    def test_facts_start_with_did_you_know(self):
        """Test that facts start with 'Did you know?'"""
        service = FactQuirkService()

        # Check all fact collections
        all_facts = (
            service.SCIENCE_FACTS +
            service.ANIMAL_FACTS +
            service.SPACE_FACTS +
            service.NATURE_FACTS +
            service.HISTORY_FACTS +
            service.TECH_FACTS +
            service.BODY_FACTS +
            service.GEOGRAPHY_FACTS +
            service.GENERAL_FACTS
        )

        # All should start with "Did you know?"
        for fact in all_facts:
            assert fact.startswith("Did you know?")
            assert len(fact) > 20  # Should be substantive

    def test_facts_are_educational(self):
        """Test that facts contain educational content"""
        service = FactQuirkService()

        # All facts should be strings and have reasonable length
        for fact in service.SCIENCE_FACTS:
            assert isinstance(fact, str)
            assert len(fact) > 30  # Should have educational content


class TestIntegrationScenarios:
    """Test realistic integration scenarios"""

    def test_science_homework_scenario(self):
        """Test fact for science homework scenario"""
        service = FactQuirkService()
        response = "I can help you with your science homework!"
        context = "I need help with science homework"
        result = service.add_fact(response, context=context, probability=1.0)

        assert "science homework" in result
        assert len(result) > len(response)
        assert "Did you know?" in result

    def test_animal_pet_scenario(self):
        """Test fact for pet scenario"""
        service = FactQuirkService()
        response = "Pets are wonderful!"
        context = "I love my cat"
        result = service.add_fact(response, context=context, probability=1.0)

        assert "Pets are wonderful" in result
        assert "Did you know?" in result

    def test_space_learning_scenario(self):
        """Test fact for space scenario"""
        service = FactQuirkService()
        response = "Space is fascinating!"
        context = "I want to learn about stars"
        result = service.add_fact(response, context=context, probability=1.0)

        assert "Space is fascinating" in result

    def test_nature_environment_scenario(self):
        """Test fact for nature scenario"""
        service = FactQuirkService()
        response = "Nature is amazing!"
        context = "I love trees"
        result = service.add_fact(response, context=context, probability=1.0)

        assert "Nature is amazing" in result


class TestEdgeCases:
    """Test edge cases"""

    def test_very_long_response(self):
        """Test fact addition to very long response"""
        service = FactQuirkService()
        response = "This is a very long response. " * 20
        result = service.add_fact(response, context="", probability=1.0)

        # Should handle long responses
        assert len(result) >= len(response)

    def test_response_with_special_characters(self):
        """Test response with special characters"""
        service = FactQuirkService()
        response = "It's great! How're you?"
        result = service.add_fact(response, context="", probability=1.0)

        # Should preserve special characters
        assert "It's" in result or "It" in result

    def test_multiple_keywords_in_context(self):
        """Test context with multiple keywords"""
        service = FactQuirkService()
        context = "I love animals and learning about space"
        result = service.add_fact("Cool!", context=context, probability=1.0)

        # Should handle multiple keywords gracefully
        assert "Cool!" in result
        assert len(result) > len("Cool!")
        assert "Did you know?" in result
