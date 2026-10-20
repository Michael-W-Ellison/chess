"""
Tests for where personality quirks are placed in a reply
Facts, puns and the catchphrase go before a closing question, so the reply still ends
with the bot's question.
"""

from unittest.mock import Mock, patch

import pytest

from services.conversation_manager import ConversationManager


def make_personality(quirks, catchphrase=None):
    personality = Mock()
    personality.get_quirks.return_value = quirks
    personality.friendship_level = 3
    personality.humor = 0.5
    personality.mood = "happy"
    personality.catchphrase = catchphrase
    return personality


@pytest.fixture
def manager():
    return ConversationManager()


@pytest.fixture
def always_pun():
    with patch("services.conversation_manager.pun_quirk_service.add_pun",
               side_effect=lambda response, context="", probability=0.0: f"{response} PUN!".strip()):
        yield


@pytest.fixture
def always_fact():
    with patch("services.conversation_manager.fact_quirk_service.add_fact",
               side_effect=lambda response, context="", probability=0.0: f"{response} FACT.".strip()):
        yield


class TestJokesBeforeQuestions:
    def test_pun_goes_before_closing_question(self, manager, always_pun):
        response = manager._apply_personality_filter(
            "That's awesome! What was the best part?", make_personality(["tells_puns"]))
        assert response == "That's awesome! PUN! What was the best part?"

    def test_fact_goes_before_closing_question(self, manager, always_fact):
        response = manager._apply_personality_filter(
            "Cool! Do you like it?", make_personality(["shares_facts"]))
        assert response == "Cool! FACT. Do you like it?"

    def test_several_closing_questions_stay_together(self, manager, always_pun):
        response = manager._apply_personality_filter(
            "Nice! Do you? What about you?", make_personality(["tells_puns"]))
        assert response == "Nice! PUN! Do you? What about you?"

    def test_question_inside_the_reply_is_not_moved(self, manager, always_pun):
        response = manager._apply_personality_filter(
            "You won your game? That's awesome!", make_personality(["tells_puns"]))
        assert response == "You won your game? That's awesome! PUN!"

    def test_reply_without_question_still_ends_with_joke(self, manager, always_pun):
        response = manager._apply_personality_filter("That's awesome!", make_personality(["tells_puns"]))
        assert response == "That's awesome! PUN!"

    def test_reply_that_is_only_a_question_gets_no_joke(self, manager, always_pun, always_fact):
        features = {}
        response = manager._apply_personality_filter(
            "Wait, who do you mean?", make_personality(["tells_puns", "shares_facts"]), features=features)
        assert response == "Wait, who do you mean?"
        assert "humor" not in features

    def test_humor_feature_is_recorded(self, manager, always_pun):
        features = {}
        manager._apply_personality_filter(
            "Cool! What's yours?", make_personality(["tells_puns"]), features=features)
        assert features["humor"] == "pun"


class TestCatchphrasePlacement:
    @pytest.fixture(autouse=True)
    def catchphrase_on(self):
        with patch("services.conversation_manager.can_use_catchphrase", return_value=True), \
                patch("random.random", return_value=0.0):
            yield

    def test_catchphrase_goes_before_closing_question(self, manager):
        response = manager._apply_personality_filter(
            "Nice! What did you do next?", make_personality([], catchphrase="Cool beans!"))
        assert response == "Nice! Cool beans! What did you do next?"

    def test_emoji_after_question_stays_with_question(self, manager):
        with patch("services.conversation_manager.emoji_quirk_service.apply_emojis",
                   side_effect=lambda response, mood=None, intensity=0.0: response.replace("yours?", "yours? 😄")):
            response = manager._apply_personality_filter(
                "Cool! What's yours?", make_personality(["uses_emojis"], catchphrase="Cool beans!"))
        assert response == "Cool! Cool beans! What's yours? 😄"

    def test_catchphrase_at_end_without_question(self, manager):
        response = manager._apply_personality_filter(
            "This is fun", make_personality([], catchphrase="Awesome!"))
        assert response == "This is fun Awesome!"


@pytest.mark.parametrize("text,expected", [
    ("Cool! What's yours? 😄", ("Cool!", "What's yours? 😄")),
    ("This is fun", ("This is fun", "")),
    ("Wait, who do you mean?", ("", "Wait, who do you mean?")),
    ("What do you call a sad strawberry? A blue-berry!", ("What do you call a sad strawberry? A blue-berry!", "")),
    ("", ("", "")),
])
def test_split_closing_question(text, expected):
    assert ConversationManager._split_closing_question(text) == expected
