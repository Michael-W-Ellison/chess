"""
Corrections from the child ("no its Sammy", "oops his name is Rex", "I didn't say that"):
detection (services/correction_handler.py) needs no spaCy model; the conversations through
the API (memories changed or removed, the bot's reply) are skipped when spaCy or its English
model is not installed.
"""

import logging
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from main import app
from services import correction_handler
from services.conversation_manager import conversation_manager
from services.correction_handler import NOT_NAME, REPLACE, RETRACT, detect
from services.utterance_parser import UtteranceParser

needs_model = pytest.mark.skipif(
    not UtteranceParser().is_available(), reason="spaCy model en_core_web_sm not installed"
)


@pytest.mark.parametrize("message,kind,value", [
    ("no its sammy", REPLACE, "sammy"),
    ("No, it's Sammy!", REPLACE, "sammy"),
    ("oops his name is rex", REPLACE, "rex"),
    ("oops i meant a cat", REPLACE, "a cat"),
    ("i said frogs", REPLACE, "frogs"),
    ("not dogs, cats", REPLACE, "cats"),
    ("his name is actually rex", REPLACE, "rex"),
    ("no wait im 8", REPLACE, None),
    ("i didnt say that", RETRACT, None),
    ("i didnt say that i said frogs", RETRACT, "frogs"),
    ("thats not what i said", RETRACT, None),
    ("thats not my name", NOT_NAME, None),
    ("my name isnt lily its lila", NOT_NAME, "lila"),
])
def test_detects_corrections(message, kind, value):
    correction = detect(message)
    assert correction is not None and (correction.kind, correction.value) == (kind, value)


@pytest.mark.parametrize("message", [
    "no she works there", "no thanks", "i said sorry to my sister", "jk ur cool", "no it was fun", "wait what",
])
def test_a_sentence_after_the_cue_is_not_a_new_value(message):
    correction = detect(message)
    assert correction is None or correction.value is None


@pytest.mark.parametrize("message", ["no", "nope", "i didnt mean it", "its lila", "my dog is named max"])
def test_not_corrections(message):
    assert detect(message) is None


def test_a_plain_no_can_answer_a_yes_no_question():
    assert detect("nope, burgers").plain_no and not detect("no wait its sammy").plain_no
    assert correction_handler.asks_yes_no("Pizza is great! Do you like tacos too?")
    assert not correction_handler.asks_yes_no("Nice to meet you, Sam! What do you like to do for fun?")


@pytest.fixture(scope="module")
def api():
    logging.disable(logging.CRITICAL)
    with patch("utils.config.settings.USE_LLM", False), TestClient(app) as client:
        yield client
    logging.disable(logging.NOTSET)


class Child:
    """One child talking to the bot through the API"""

    def __init__(self, api, user_id):
        self.api, self.user_id = api, user_id
        self.start()

    def start(self):
        response = self.api.post(f"/api/conversation/start?user_id={self.user_id}")
        assert response.status_code == 200
        self.conversation_id = response.json()["conversation_id"]

    def say(self, text):
        response = self.api.post("/api/message", json={
            "content": text, "conversation_id": self.conversation_id, "user_id": self.user_id})
        assert response.status_code == 200
        return response.json()["content"]

    def memories(self):
        response = self.api.get(f"/api/profile/memories?user_id={self.user_id}")
        assert response.status_code == 200
        return {m["key"]: m["value"] for m in response.json()["memories"]}


@needs_model
def test_name_corrected_without_a_cue_word(api):
    child = Child(api, 7301)
    child.say("my name is sam")
    assert "Sammy" in child.say("no its sammy")
    assert child.memories()["name"] == "Sammy"
    assert "Sammy" in child.say("whats my name")


@needs_model
def test_wrong_name_is_forgotten_and_asked_again(api):
    child = Child(api, 7302)
    child.say("im Lily")
    assert "What's your name?" in child.say("my name isnt lily")
    assert "name" not in child.memories()
    child.say("its lila")
    assert child.memories()["name"] == "Lila"


@needs_model
def test_pet_name_corrected(api):
    child = Child(api, 7303)
    child.say("i have a dog named max")
    assert "Rex" in child.say("oops his name is rex")
    memories = child.memories()
    assert memories.get("dog_rex") == "Rex" and "dog_max" not in memories
    assert "Rex" in child.say("whats my dogs name")


@needs_model
def test_pet_name_corrected_in_a_later_conversation(api):
    child = Child(api, 7304)
    child.say("i have a dog named max")
    child.say("bye")
    child.start()
    child.say("his name is actually rex")
    assert "dog_max" not in child.memories() and child.memories().get("dog_rex") == "Rex"


@needs_model
def test_meant_something_else(api):
    child = Child(api, 7305)
    child.say("i have a dog")
    assert "cat" in child.say("oops i meant a cat")
    memories = child.memories()
    assert memories.get("has_cat") == "a cat" and "has_dog" not in memories


@needs_model
def test_opposite_replaces_a_like(api):
    child = Child(api, 7306)
    child.say("i like broccoli")
    child.say("actually i hate broccoli")
    child.say("do i like broccoli")  # a question stores nothing
    memories = child.memories()
    assert memories.get("dislikes_broccoli") == "broccoli" and "likes_broccoli" not in memories


@needs_model
def test_restated_age_is_acknowledged(api):
    child = Child(api, 7307)
    child.say("im 7")
    assert "8" in child.say("no wait im 8")
    assert child.memories()["age"] == "8"


@needs_model
def test_retracted_memory_is_removed_and_the_answer_stored(api):
    child = Child(api, 7308)
    child.say("i like dogs")
    assert "forget" in child.say("i didnt say that")
    assert "likes_dogs" not in child.memories()
    assert "frogs" in child.say("i said frogs")
    assert child.memories().get("likes_frogs") == "frogs"


@needs_model
def test_retracting_an_update_restores_the_old_value(api):
    child = Child(api, 7309)
    child.say("my favorite color is blue")
    child.say("my favorite color is red")
    child.say("i didnt say that")
    assert child.memories()["favorite_color"] == "blue"


@needs_model
def test_no_answering_a_yes_no_question_is_not_a_correction(api):
    child = Child(api, 7310)
    child.say("i like pizza")
    conversation_manager._last_reply[child.user_id] = "Pizza is great! Do you like tacos too?"
    child.say("no, burgers")
    assert child.memories().get("likes_pizza") == "pizza"
