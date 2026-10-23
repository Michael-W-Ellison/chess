"""
Tests for where personality quirks are placed in a reply
A fact or pun is only added to a reply without a closing question, never to two replies in
a row, and after the emojis; the catchphrase goes before a closing question.
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


class TestJokePlacement:
    @pytest.mark.parametrize("reply", [
        "That's awesome! What was the best part?",
        "Nice! Do you? What about you?",
        "Wait, who do you mean?",
        "That's awesome! Tell me more!",
        "Cool! Tell me more about that. 😄",
    ])
    def test_reply_asking_a_question_gets_no_joke(self, manager, always_pun, always_fact, reply):
        features = {}
        response = manager._apply_personality_filter(
            reply, make_personality(["tells_puns", "shares_facts"]), features=features)
        assert response == reply
        assert "humor" not in features

    def test_question_inside_the_reply_is_not_moved(self, manager, always_pun):
        response = manager._apply_personality_filter(
            "You won your game? That's awesome!", make_personality(["tells_puns"]))
        assert response == "You won your game? That's awesome! PUN!"

    def test_reply_without_question_ends_with_joke(self, manager, always_pun):
        response = manager._apply_personality_filter("That's awesome!", make_personality(["tells_puns"]))
        assert response == "That's awesome! PUN!"

    def test_humor_feature_is_recorded(self, manager, always_pun):
        features = {}
        manager._apply_personality_filter("Cool!", make_personality(["tells_puns"]), features=features)
        assert features["humor"] == "pun"

    def test_no_jokes_in_two_replies_in_a_row(self, manager, always_pun):
        personality = make_personality(["tells_puns"])
        first = manager._apply_personality_filter("Cool!", personality)
        second = manager._apply_personality_filter("Nice!", personality)
        third = manager._apply_personality_filter("Great!", personality)
        assert (first, second, third) == ("Cool! PUN!", "Nice!", "Great! PUN!")

    def test_joke_cooldown_is_per_user(self, manager, always_pun):
        manager._apply_personality_filter("Cool!", make_personality(["tells_puns"]))
        assert manager._apply_personality_filter("Nice!", make_personality(["tells_puns"])) == "Nice! PUN!"

    def test_emojis_never_split_a_joke(self, manager):
        personality = make_personality(["tells_puns", "uses_emojis"])
        personality.friendship_level = 10  # most emojis
        with patch.object(ConversationManager, "_choose_joke", return_value="pun"), \
                patch("services.conversation_manager.pun_quirk_service.add_pun",
                      side_effect=lambda r, context="", probability=0.0: f"{r} Why did it cross? To get over!"):
            for _ in range(50):
                manager._joked_last_reply.clear()
                response = manager._apply_personality_filter("That's awesome! You did great.", personality)
                assert response.endswith("Why did it cross? To get over!")


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
            manager._joked_last_reply.clear()
            response = manager._apply_personality_filter(
                "That's awesome! You did great.", self.personality(), "soccer", features=features)
            has_pun = any(p[1:] in response for p in puns)
            has_fact = any(f[1:] in response for f in facts)
            assert not (has_pun and has_fact)
            assert "  " not in response


def test_every_pun_has_a_lead_in():
    from services.pun_quirk_service import pun_quirk_service
    import random
    random.seed(0)
    for _ in range(50):
        response = pun_quirk_service.add_pun("Cool!", probability=1.0)
        assert response.split("Cool! ", 1)[1].startswith(("Oh, and here's", "Here's"))
        assert "reminds me" not in response and "Speaking of which" not in response


def test_name_introduction_gets_no_jokes():
    from services.response_engine import response_engine
    assert response_engine.rule_flag("name_is", "no_jokes")
