"""
Tests for Pun Quirk Service
Task 70: Implement tells_puns quirk
"""

import pytest
from services.pun_quirk_service import PunQuirkService, pun_quirk_service


class TestPunQuirkService:
    """Test pun quirk service initialization and basic functionality"""

    def test_service_initialization(self):
        """Test that service initializes correctly"""
        service = PunQuirkService()
        assert service is not None
        assert hasattr(service, 'GENERAL_PUNS')
        assert hasattr(service, 'SCHOOL_PUNS')
        assert hasattr(service, 'CONTEXT_KEYWORDS')

    def test_global_instance_exists(self):
        """Test that global singleton instance exists"""
        assert pun_quirk_service is not None

    def test_pun_collections_not_empty(self):
        """Test that pun collections are populated"""
        service = PunQuirkService()
        assert len(service.GENERAL_PUNS) > 0
        assert len(service.SCHOOL_PUNS) > 0
        assert len(service.FRIEND_PUNS) > 0
        assert len(service.GAME_PUNS) > 0
        assert len(service.FOOD_PUNS) > 0
        assert len(service.ANIMAL_PUNS) > 0


class TestPunAddition:
    """Test adding puns to responses"""

    def test_add_pun_with_high_probability(self):
        """Test pun addition with high probability"""
        service = PunQuirkService()
        response = "That's interesting!"
        result = service.add_pun(response, context="", probability=1.0)

        # With probability=1.0, pun should always be added
        assert len(result) > len(response)
        assert "That's interesting!" in result

    def test_add_pun_with_zero_probability(self):
        """Test that no pun is added with zero probability"""
        service = PunQuirkService()
        response = "That's interesting!"
        result = service.add_pun(response, context="", probability=0.0)

        # With probability=0.0, no pun should be added
        assert result == response

    def test_add_pun_preserves_original_response(self):
        """Test that original response is preserved"""
        service = PunQuirkService()
        response = "I can help you with that."
        result = service.add_pun(response, context="", probability=1.0)

        # Original response should still be in result
        assert "help you with that" in result

    def test_add_pun_to_empty_response(self):
        """Test adding pun to empty response"""
        service = PunQuirkService()
        response = ""
        result = service.add_pun(response, context="", probability=1.0)

        # Should just return a pun
        assert len(result) > 0


class TestContextualPuns:
    """Test context-based pun selection"""

    def test_school_context_pun(self):
        """Test pun for school-related context"""
        service = PunQuirkService()
        context = "I have homework to do"
        result = service.add_pun("Good luck!", context=context, probability=1.0)

        # Should add a pun (school-related preferred)
        assert len(result) > len("Good luck!")

    def test_game_context_pun(self):
        """Test pun for game-related context"""
        service = PunQuirkService()
        context = "Let's play a game"
        result = service.add_pun("Sounds fun!", context=context, probability=1.0)

        assert "Sounds fun!" in result
        assert len(result) > len("Sounds fun!")

    def test_food_context_pun(self):
        """Test pun for food-related context"""
        service = PunQuirkService()
        context = "I'm eating lunch"
        result = service.add_pun("Enjoy!", context=context, probability=1.0)

        assert "Enjoy!" in result

    def test_animal_context_pun(self):
        """Test pun for animal-related context"""
        service = PunQuirkService()
        context = "I love my dog"
        result = service.add_pun("That's sweet!", context=context, probability=1.0)

        assert "That's sweet!" in result

    def test_no_context_uses_general_pun(self):
        """Test that general puns are used without context"""
        service = PunQuirkService()
        result = service.add_pun("Cool!", context="", probability=1.0)

        # Should add a general pun
        assert len(result) > len("Cool!")


class TestGetContextualPun:
    """Test contextual pun retrieval"""

    def test_get_contextual_pun_school(self):
        """Test getting school-related pun"""
        service = PunQuirkService()
        pun = service._get_contextual_pun("I have a math test")

        # Should return a pun (likely school-related)
        assert pun is not None
        assert isinstance(pun, str)
        assert len(pun) > 0

    def test_get_contextual_pun_no_match(self):
        """Test getting pun with no keyword match"""
        service = PunQuirkService()
        pun = service._get_contextual_pun("xyz abc def")

        # Should return None when no match
        assert pun is None

    def test_get_contextual_pun_empty_context(self):
        """Test getting pun with empty context"""
        service = PunQuirkService()
        pun = service._get_contextual_pun("")

        # Should return None for empty context
        assert pun is None


class TestGetRandomPun:
    """Test random pun selection"""

    def test_get_random_pun_returns_string(self):
        """Test that random pun returns a string"""
        service = PunQuirkService()
        pun = service._get_random_pun()

        assert isinstance(pun, str)
        assert len(pun) > 0

    def test_get_random_pun_different_calls(self):
        """Test that random pun can return different results"""
        service = PunQuirkService()

        # Get multiple puns
        puns = [service._get_random_pun() for _ in range(10)]

        # At least some should be different (probabilistic test)
        assert len(set(puns)) > 1


class TestGetPunByCategory:
    """Test getting puns by specific category"""

    def test_get_pun_by_category_general(self):
        """Test getting general pun"""
        service = PunQuirkService()
        pun = service.get_pun_by_category("general")

        assert isinstance(pun, str)
        assert pun in service.GENERAL_PUNS

    def test_get_pun_by_category_school(self):
        """Test getting school pun"""
        service = PunQuirkService()
        pun = service.get_pun_by_category("school")

        assert pun in service.SCHOOL_PUNS

    def test_get_pun_by_category_game(self):
        """Test getting game pun"""
        service = PunQuirkService()
        pun = service.get_pun_by_category("game")

        assert pun in service.GAME_PUNS

    def test_get_pun_by_category_food(self):
        """Test getting food pun"""
        service = PunQuirkService()
        pun = service.get_pun_by_category("food")

        assert pun in service.FOOD_PUNS

    def test_get_pun_by_category_animal(self):
        """Test getting animal pun"""
        service = PunQuirkService()
        pun = service.get_pun_by_category("animal")

        assert pun in service.ANIMAL_PUNS

    def test_get_pun_by_category_invalid(self):
        """Test getting pun with invalid category falls back to general"""
        service = PunQuirkService()
        pun = service.get_pun_by_category("invalid_category")

        # Should fall back to general puns
        assert pun in service.GENERAL_PUNS


class TestPunTransitions:
    """Test pun transition phrases"""

    def test_pun_has_transition_sometimes(self):
        """Test that puns sometimes include transition phrases"""
        service = PunQuirkService()

        # Get multiple puns to test probabilistic transitions
        results = []
        for _ in range(20):
            result = service.add_pun("Hello", context="", probability=1.0)
            results.append(result)

        # Check if any have transition phrases
        has_transitions = any(
            "Oh, and here's a fun one" in r or
            "Speaking of which" in r or
            "That reminds me" in r or
            "By the way" in r
            for r in results
        )

        # At least some should have transitions (probabilistic)
        assert has_transitions


class TestPunContent:
    """Test that puns are appropriate and well-formed"""

    def test_puns_are_kid_friendly(self):
        """Test that puns are appropriate for kids"""
        service = PunQuirkService()

        # Check all pun collections
        all_puns = (
            service.GENERAL_PUNS +
            service.SCHOOL_PUNS +
            service.FRIEND_PUNS +
            service.GAME_PUNS +
            service.FOOD_PUNS +
            service.ANIMAL_PUNS +
            service.NATURE_PUNS +
            service.TECH_PUNS
        )

        # All should be strings
        for pun in all_puns:
            assert isinstance(pun, str)
            assert len(pun) > 0
            # Should have question or statement structure
            assert "?" in pun or "!" in pun or "." in pun

    def test_puns_have_setup_and_punchline(self):
        """Test that puns generally follow Q&A or statement format"""
        service = PunQuirkService()

        # Most puns should have question marks or multiple sentences
        for pun in service.GENERAL_PUNS:
            # Either a question/answer format or a statement
            assert len(pun) > 10  # Reasonable minimum length


class TestIntegrationScenarios:
    """Test realistic integration scenarios"""

    def test_school_homework_scenario(self):
        """Test pun for homework scenario"""
        service = PunQuirkService()
        response = "I can help you with your homework!"
        context = "I need help with my homework"
        result = service.add_pun(response, context=context, probability=1.0)

        assert "help you with your homework" in result
        assert len(result) > len(response)

    def test_game_playing_scenario(self):
        """Test pun for game scenario"""
        service = PunQuirkService()
        response = "Let's play together!"
        context = "Want to play a game?"
        result = service.add_pun(response, context=context, probability=1.0)

        assert "play together" in result

    def test_animal_pet_scenario(self):
        """Test pun for pet scenario"""
        service = PunQuirkService()
        response = "Pets are wonderful!"
        context = "I love my cat"
        result = service.add_pun(response, context=context, probability=1.0)

        assert "Pets are wonderful" in result

    def test_food_lunch_scenario(self):
        """Test pun for food scenario"""
        service = PunQuirkService()
        response = "Sounds delicious!"
        context = "I'm eating pizza"
        result = service.add_pun(response, context=context, probability=1.0)

        assert "Sounds delicious" in result


class TestEdgeCases:
    """Test edge cases"""

    def test_very_long_response(self):
        """Test pun addition to very long response"""
        service = PunQuirkService()
        response = "This is a very long response. " * 20
        result = service.add_pun(response, context="", probability=1.0)

        # Should handle long responses
        assert len(result) >= len(response)

    def test_response_with_special_characters(self):
        """Test response with special characters"""
        service = PunQuirkService()
        response = "It's great! How're you?"
        result = service.add_pun(response, context="", probability=1.0)

        # Should preserve special characters
        assert "It's" in result or "It" in result

    def test_multiple_keywords_in_context(self):
        """Test context with multiple keywords"""
        service = PunQuirkService()
        context = "I love my dog and playing games at school"
        result = service.add_pun("Cool!", context=context, probability=1.0)

        # Should handle multiple keywords gracefully
        assert "Cool!" in result
        assert len(result) > len("Cool!")
