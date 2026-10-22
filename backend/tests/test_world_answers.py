"""
Tests for the answers to common questions about the world (knowledge/answers.json)
Skipped when spaCy or its English model is not installed.
"""

import json
import random
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

from services.response_engine import ResponseEngine
from services.utterance_parser import UtteranceParser

ANSWERS = json.loads((Path(__file__).resolve().parent.parent / "knowledge" / "answers.json").read_text())["answers"]


def test_every_pattern_compiles_and_has_an_answer():
    for entry in ANSWERS:
        re.compile(entry["pattern"])
        assert entry["answer"].strip()


needs_parser = pytest.mark.skipif(
    not UtteranceParser().is_available(), reason="spaCy model en_core_web_sm not installed"
)


@pytest.fixture
def engine():
    return ResponseEngine(rng=random.Random(0))


def reply(engine, message):
    personality = SimpleNamespace(id=1, user_id=1, name="Buddy", mood="happy", friendship_level=1,
                                  energy=0.7, curiosity=0.0, formality=0.3, get_interests=lambda: [])
    features = {}
    text = engine.generate_response(message, personality, features=features)
    return text, features.get("rule")


@needs_parser
@pytest.mark.parametrize("question,start", [
    ("why is the sky blue", "The sky looks blue"),
    ("how far is the moon?", "The Moon is about 239,000 miles"),
    ("how many bones do we have", "Grown-ups have 206 bones"),
    ("why do cats purr", "Cats often purr"),
    ("who invented the light bulb", "Thomas Edison"),
    ("how many legs does a spider have", "Spiders have 8 legs"),
    ("why can't penguins fly", "Penguins can't fly"),
    ("what is a black hole", "A black hole"),
    ("do you know why the sky is blue", "The sky looks blue"),
    ("where do babies come from", "That's a great question to ask"),
])
def test_known_questions(engine, question, start):
    text, rule = reply(engine, question)
    assert rule == "fallback_world_answer"
    assert text.startswith(start)


@needs_parser
def test_questions_about_the_bot_are_not_world_questions(engine):
    text, rule = reply(engine, "why do you like pizza")
    assert rule == "bot_why_like"
