"""
Statements about the world checked against knowledge/facts.json (ResponseEngine.check_fact,
_fact_reply): a wrong one is disputed, a right one confirmed, and "you're wrong" right after
gets the bot sticking to the fact. Needs no spaCy model for the fact checks; the replies
through generate_response are skipped when spaCy or its English model is not installed.
"""

import json
import random
from pathlib import Path

import pytest

from services.response_engine import ResponseEngine
from services.utterance_parser import UtteranceParser
from tests.test_dialogue_fixes import make_personality

FACTS = json.loads((Path(__file__).resolve().parent.parent / "knowledge" / "facts.json").read_text("utf-8"))
# The hand-written facts' examples, one test each (the generated ones are checked together below)
EXAMPLES = [(fact["id"], message, verdict) for fact in FACTS["facts"] for message, verdict in fact.get("examples", [])]
needs_model = pytest.mark.skipif(not UtteranceParser().is_available(), reason="spaCy model en_core_web_sm not installed")


@pytest.fixture(scope="module")
def engine():
    return ResponseEngine(rng=random.Random(0))


@pytest.mark.parametrize("fact_id,message,verdict", EXAMPLES)
def test_fact_example(engine, fact_id, message, verdict):
    checked = engine.check_fact(message)
    if verdict is None:
        assert checked is None
    else:
        assert checked is not None and checked[0]["id"] == fact_id
        assert checked[1] == (verdict == "right")


@pytest.mark.parametrize("fact", FACTS["facts"], ids=lambda f: f["id"])
def test_fact_is_described(fact):
    assert fact.get("correct") and fact.get("examples")
    assert any(verdict == "wrong" for _, verdict in fact["examples"])


def test_generated_facts_are_up_to_date_and_answer_their_examples():
    """The "generated" facts are what scripts/build_facts.py makes from its tables, and pass its checks"""
    import importlib.util
    path = Path(__file__).resolve().parent.parent / "scripts" / "build_facts.py"
    spec = importlib.util.spec_from_file_location("build_facts", path)
    build_facts = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build_facts)
    sets, generated, _, problems = build_facts.generate({k: v for k, v in FACTS.items() if k != "generated"})
    assert problems == []
    assert FACTS["sets"] == sets, "run python scripts/build_facts.py"
    assert FACTS["generated"] == generated, "run python scripts/build_facts.py"
    assert len(generated) > 4000
    # Mostly science: no more than 21 number facts (0 to 20)
    assert sum(f["id"].startswith("number_") for f in generated) == 21
    assert all(f.get("correct") and any(v == "wrong" for _, v in f["examples"]) for f in generated)


@pytest.mark.parametrize("message,fact_id,right", [
    ("the capital of australia is sydney", "capital_australia", False),
    ("sydney is the capital of australia", "not_capital_sydney", False),
    ("the capital of the usa is new york", "capital_the_united_states", False),
    ("mercury is the hottest planet", "most_hottest_planet", False),
    ("the cheetah is the fastest animal", "most_fastest_animal", False),
    ("africa is a country", "kind_africa", False),
    ("lions are herbivores", "diet_lion", False),
    ("a baby kangaroo is a joey", "baby_kangaroo", True),
    ("dolphins can breathe underwater", "breathe_dolphin", False),
    ("february has 30 days", "month_days_february", False),
    ("9 is a prime number", "number_9", False),
    ("brazil is in south america", "continent_brazil", True),
    ("platypuses dont lay eggs", "eggs_platypus", False),
    ("dogs lay eggs", "eggs_dog", False),
    ("snakes are warm blooded", "blood_snake", False),
    ("whales have gills", "gills_whale", False),
    ("jellyfish are fish", "class_jellyfish", False),
    ("the sun goes around the earth", "orbit_sun_earth", False),
    ("the moon makes its own light", "light_moon", False),
    ("magnets attract wood", "magnet_wood", False),
    ("ice is a liquid", "matter_ice", False),
    ("mushrooms are plants", "mushroom_fungus", False),
    ("blood is blue", "blood_red", False),
    ("dinosaurs lived with people", "dinosaurs_people", False),
    ("t rex ate plants", "dino_not_ate_t_rex", False),
    ("pterodactyls are dinosaurs", "pterodactyl_reptile", False),
    ("sound can travel in space", "sound_space", False),
])
def test_generated_facts(engine, message, fact_id, right):
    checked = engine.check_fact(message)
    assert checked is not None and (checked[0]["id"], checked[1]) == (fact_id, right)


@pytest.mark.parametrize("message", ["dogs fly kites", "jordan is mean", "chad is in my class", "10 is a lot",
                                     "green is my favorite", "birds fly south", "the best day is saturday"])
def test_everyday_statements_are_not_checked(engine, message):
    assert engine.check_fact(message) is None


@pytest.mark.parametrize("message", [
    "how many legs does a spider have", "do penguins fly?", "in my game penguins can fly", "my dog has 3 legs",
    "i have 2 dogs", "some spiders have 6 legs", "pretend the sky is green", "i wish penguins could fly",
    "the sun is shining", "grass is wet", "there are 9 kids in my class",
])
def test_not_statements_about_facts(engine, message):
    assert engine.check_fact(message) is None


def reply(engine, message, user_id=1):
    features = {}
    text = engine.generate_response(message, make_personality(), features=features)
    return features.get("rule"), text


@needs_model
def test_wrong_fact_is_disputed():
    engine = ResponseEngine(rng=random.Random(0))
    rule, text = reply(engine, "spiders have 6 legs")
    assert rule == "fact_spider_legs" and "8 legs" in text
    assert text.startswith(("Hmm, I don't think that's right!", "Actually, I learned something different:"))


@needs_model
def test_right_fact_is_confirmed():
    engine = ResponseEngine(rng=random.Random(0))
    rule, text = reply(engine, "whales are mammals")
    assert rule == "fact_whale_mammal" and text.startswith(("That's right!", "Yep, you got it!"))


@needs_model
@pytest.mark.parametrize("pushback", ["you're wrong", "yes they do", "nope", "thats not true"])
def test_bot_sticks_to_the_fact(pushback):
    engine = ResponseEngine(rng=random.Random(0))
    reply(engine, "penguins can fly")
    rule, text = reply(engine, pushback)
    assert rule == "fact_insist" and "can't fly" in text


@needs_model
def test_bot_sticks_to_its_world_answer():
    engine = ResponseEngine(rng=random.Random(0))
    first, _ = reply(engine, "how many legs does a spider have")
    assert first == "fallback_world_answer"
    assert reply(engine, "you're wrong")[0] == "fact_insist"


@needs_model
def test_pushback_without_a_fact_is_not_insisted_on():
    engine = ResponseEngine(rng=random.Random(0))
    reply(engine, "i like pizza")
    assert reply(engine, "you're wrong")[0] != "fact_insist"


@needs_model
@pytest.mark.parametrize("first,answer,rule", [
    ("there are 9 planets", "no there are 9", "fact_insist"),
    ("there are 9 planets", "oh there are 8", "fact_planets"),
    ("penguins can fly", "yes they can", "fact_insist"),
    ("penguins can fly", "oh they cant", "fact_penguins_fly"),
    ("the capital of australia is sydney", "no its sydney", "fact_insist"),
    ("the capital of australia is sydney", "oh its canberra", "fact_capital_australia"),
])
def test_short_answer_after_a_fact_is_checked(first, answer, rule):
    engine = ResponseEngine(rng=random.Random(0))
    reply(engine, first)
    assert reply(engine, answer)[0] == rule


@needs_model
@pytest.mark.parametrize("message,expected", [
    ("2 plus 2 is 5", "Hmm, let me check... 2 plus 2 is 4, not 5!"),
    ("3 times 3 equals 9", "That's right! 3 times 3 is 9. Nice math!"),
])
def test_stated_sum_is_checked(message, expected):
    engine = ResponseEngine(rng=random.Random(0))
    rule, text = reply(engine, message)
    assert rule == "arithmetic_check" and text == expected
