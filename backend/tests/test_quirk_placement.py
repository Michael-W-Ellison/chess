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
    with patch.object(ConversationManager, "_choose_joke", return_value="pun"), \
            patch("services.conversation_manager.pun_quirk_service.add_pun",
                  side_effect=lambda response, context="", probability=0.0: f"{response} PUN!".strip()):
        yield


@pytest.fixture
def always_fact():
    with patch.object(ConversationManager, "_choose_joke", return_value="fact"), \
            patch("services.conversation_manager.fact_quirk_service.add_fact",
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


def test_jokes_can_be_turned_off(manager, always_pun, always_fact):
    """Used when the reply is already a requested joke or fact"""
    features = {}
    response = manager._apply_personality_filter(
        "Okay, here's one: Why did the cookie cry? Its mom was a wafer so long!",
        make_personality(["tells_puns", "shares_facts"]), features=features, allow_jokes=False)
    assert "PUN" not in response and "FACT" not in response
    assert "humor" not in features


class TestOneJokePerReply:
    @staticmethod
    def personality(humor=1.0, level=10):
        personality = make_personality(["tells_puns", "shares_facts"])
        personality.humor = humor
        personality.friendship_level = level
        return personality

    def test_choose_joke_never_returns_both_and_is_capped(self):
        import random
        from services.conversation_manager import MAX_JOKE_PROBABILITY
        random.seed(0)
        choices = [ConversationManager._choose_joke(["tells_puns", "shares_facts"], self.personality(), 1.5)
                   for _ in range(2000)]
        assert set(choices) <= {"pun", "fact", None}
        joke_rate = sum(c is not None for c in choices) / len(choices)
        assert joke_rate == pytest.approx(MAX_JOKE_PROBABILITY, abs=0.04)

    def test_no_quirks_no_joke(self):
        assert ConversationManager._choose_joke([], self.personality(), 1.0) is None

    def test_only_enabled_quirk_is_used(self):
        import random
        random.seed(1)
        choices = {ConversationManager._choose_joke(["tells_puns"], self.personality(), 1.5) for _ in range(200)}
        assert choices <= {"pun", None}

    def test_real_services_add_one_joke_at_most(self, manager):
        from services.fact_quirk_service import FactQuirkService
        from services.pun_quirk_service import PunQuirkService
        puns = [p for n in dir(PunQuirkService) if n.endswith("_PUNS") for p in getattr(PunQuirkService, n)]
        facts = [f.replace("Did you know? ", "") for n in dir(FactQuirkService) if n.endswith("_FACTS")
                 for f in getattr(FactQuirkService, n)]
        for _ in range(200):
            features = {}
            response = manager._apply_personality_filter(
                "That's awesome! What was the best part?", self.personality(), "soccer", features=features)
            has_pun = any(p[1:] in response for p in puns)
            has_fact = any(f[1:] in response for f in facts)
            assert not (has_pun and has_fact)
            assert response.endswith("What was the best part?")
            assert "  " not in response
