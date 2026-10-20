"""
Tests for pronoun resolution across turns (services/reference_tracker.py)
Skipped when spaCy or its English model is not installed.
"""

import random
from types import SimpleNamespace

import pytest

from services.reference_tracker import MAX_AGE
from services.response_engine import ResponseEngine
from services.utterance_parser import UtteranceParser

pytestmark = pytest.mark.skipif(
    not UtteranceParser().is_available(), reason="spaCy model en_core_web_sm not installed"
)

USER = 1


@pytest.fixture
def engine():
    return ResponseEngine(rng=random.Random(0))


def run(engine, *messages, user_id=USER):
    """Resolve each message in turn; return the resolved form of the last one"""
    resolved = None
    for message in messages:
        resolved = engine.resolve_references(message, user_id)
    return resolved


def personality(user_id=USER):
    return SimpleNamespace(id=1, user_id=user_id, name="Buddy", mood="happy", friendship_level=1,
                           energy=0.7, curiosity=0.0, formality=0.3, get_interests=lambda: [])


class TestPeople:
    def test_she_refers_to_named_relation(self, engine):
        resolved = run(engine, "My best friend Maya moved away", "She said no")
        assert resolved == "My best friend Maya said no"

    def test_only_first_mention_is_replaced(self, engine):
        resolved = run(engine, "My best friend Maya moved away", "She said she would call me")
        assert resolved == "My best friend Maya said she would call me"

    def test_object_pronoun(self, engine):
        assert run(engine, "My best friend Maya moved away", "I miss her") == "I miss my best friend Maya"

    def test_possessive_pronoun(self, engine):
        resolved = run(engine, "My best friend Maya moved away", "Her mom is nice")
        assert resolved == "My best friend Maya's mom is nice"

    def test_relation_without_name(self, engine):
        assert run(engine, "My teacher gave us a test", "She yelled at me") == "My teacher yelled at me"

    def test_name_from_copula(self, engine):
        assert run(engine, "Jake is my brother", "He broke my tower") == "My brother Jake broke my tower"

    def test_they_refers_to_a_group(self, engine):
        assert run(engine, "I played with Maya and Jake", "They were fun") == "Maya and Jake were fun"

    def test_they_refers_to_plural_relation(self, engine):
        assert run(engine, "My parents took me to the zoo", "They are the best") == "My parents are the best"

    def test_pronoun_choice_is_learned_per_person(self, engine):
        run(engine, "I played with Maya", "She was nice")  # the child used "she" for Maya
        run(engine, "Maya and Jake came over")
        assert run(engine, "He was mean") == "Jake was mean"
        assert run(engine, "She was funny") == "Maya was funny"

    def test_untagged_name_as_object_of_social_verb(self, engine):
        assert run(engine, "I saw Maya at school", "She waved at me") == "Maya waved at me"

    def test_game_name_is_not_a_person(self, engine):
        assert run(engine, "I played Minecraft", "She was mean") == "She was mean"

    def test_unresolved_pronoun_is_left_alone(self, engine):
        assert run(engine, "She is so annoying") == "She is so annoying"

    def test_childs_own_name_is_not_a_third_person(self, engine):
        assert run(engine, "my name is Sam", "She is nice") == "She is nice"

    def test_references_expire(self, engine):
        messages = ["My best friend Maya moved away"] + ["I like pizza"] * (MAX_AGE + 1) + ["She said no"]
        assert run(engine, *messages) == "She said no"

    def test_mentioning_again_keeps_a_person_available(self, engine):
        messages = ["My best friend Maya moved away"]
        for _ in range(MAX_AGE + 1):
            messages += ["I miss her"]
        assert run(engine, *messages, "She said no") == "My best friend Maya said no"

    def test_users_are_tracked_separately(self, engine):
        run(engine, "My best friend Maya moved away", user_id=1)
        assert run(engine, "She said no", user_id=2) == "She said no"

    def test_reset_forgets_people(self, engine):
        run(engine, "My best friend Maya moved away")
        engine.reset_references(USER)
        assert run(engine, "She said no") == "She said no"


class TestThings:
    def test_it_refers_to_last_thing(self, engine):
        assert run(engine, "I have a math test tomorrow", "It was hard") == "The math test was hard"

    def test_that_refers_to_last_event(self, engine):
        assert run(engine, "We went to the zoo", "That was fun") == "Going to the zoo was fun"

    def test_it_prefers_the_thing(self, engine):
        assert run(engine, "We went to the zoo", "It was fun") == "The zoo was fun"

    def test_object_of_preference(self, engine):
        assert run(engine, "I made a new tower", "I love it") == "I love the tower"

    def test_adjectives_are_dropped(self, engine):
        assert run(engine, "My teacher gave us a hard test", "It was hard") == "The test was hard"

    def test_weather_it_is_not_resolved(self, engine):
        assert run(engine, "We went to the zoo", "It is raining") == "It is raining"

    def test_determiner_that_is_not_resolved(self, engine):
        assert run(engine, "We went to the zoo", "That game was fun") == "That game was fun"


class TestResolvedAnalysis:
    def test_rule_matches_after_resolution(self, engine):
        resolved = run(engine, "My teacher gave us a test", "She yelled at me")
        assert engine.analyze(resolved).frames[0].rule_id == "person_upset"

    def test_memory_stored_for_resolved_person(self, engine):
        resolved = run(engine, "I played with Maya", "She is my cousin")
        assert ("person", "cousin_maya", "Maya") in engine.extract_memories(resolved)

    def test_reply_names_the_person(self, engine):
        resolved = run(engine, "My best friend Maya moved away", "She said she would call me")
        reply = engine.generate_response(resolved, personality())
        assert "your best friend maya said she would call you" in reply.lower()

    def test_unresolved_person_gets_a_question(self, engine):
        reply = engine.generate_response(run(engine, "She is so annoying"), personality())
        assert reply in engine.kb["fallbacks"]["unknown_person"]

    def test_future_evaluation_reply(self, engine):
        resolved = run(engine, "I have a math test tomorrow", "I think it will be hard")
        reply = engine.generate_response(resolved, personality())
        assert "the math test will be hard" in reply and "What happened" not in reply


class TestMorePositions:
    @pytest.mark.parametrize("first,second,expected", [
        ("I made a tower out of legos", "It broke", "The tower broke"),
        ("I got a new bike", "I rode it all day", "I rode the bike all day"),
        ("We found a spider", "I'm scared of it", "I'm scared of the spider"),
        ("I have a math test tomorrow", "It made me nervous", "The math test made me nervous"),
    ])
    def test_subjects_objects_and_prepositions(self, engine, first, second, expected):
        assert run(engine, first, second) == expected

    @pytest.mark.parametrize("message", [
        "It is raining", "It's time to go", "It's my turn", "It was cold outside",
        "I made it!", "I get it", "I think that you are nice", "The game that I played was fun",
    ])
    def test_non_referring_it_and_that_are_left_alone(self, engine, message):
        assert run(engine, "We built a fort in the backyard", message) == message

    def test_main_object_outranks_detail(self, engine):
        run(engine, "I made a tower out of legos")
        assert engine.references.state(USER).things[0].text == "the tower"

    def test_contraction_after_replacement_reads_as_is(self, engine):
        assert run(engine, "We went swimming", "That's so fun") == "Going swimming is so fun"


class TestEvents:
    @pytest.mark.parametrize("first,expected", [
        ("We went swimming", "Going swimming was fun"),
        ("We went to the zoo yesterday", "Going to the zoo was fun"),
        ("I baked cookies with my mom", "Baking cookies with my mom was fun"),
        ("We played tag at recess", "Playing tag at recess was fun"),
    ])
    def test_that_refers_to_what_the_child_did(self, engine, first, expected):
        assert run(engine, first, "That was fun") == expected

    def test_questions_and_states_are_not_events(self, engine):
        run(engine, "Do you like pizza?")
        run(engine, "I feel tired")
        assert engine.references.state(USER).events == []

    @pytest.mark.parametrize("lemma,expected", [
        ("go", "going"), ("swim", "swimming"), ("bake", "baking"), ("lie", "lying"),
        ("see", "seeing"), ("visit", "visiting"), ("play", "playing"), ("run", "running"),
    ])
    def test_gerund(self, lemma, expected):
        from services.reference_tracker import gerund
        assert gerund(lemma) == expected


class TestBotReplies:
    def reply_and_record(self, engine, message, user_id=USER):
        resolved = engine.resolve_references(message, user_id)
        reply = engine.generate_response(resolved, personality(user_id))
        engine.record_bot_reply(user_id, reply)
        return reply

    def test_that_refers_to_the_fact_the_bot_told(self, engine):
        self.reply_and_record(engine, "tell me a fun fact")
        assert run(engine, "That's so cool") == "Your fun fact is so cool"

    def test_joke_added_by_quirk_filter(self, engine):
        engine.resolve_references("I like soccer", USER)
        engine.record_bot_reply(USER, "You like soccer? Nice!", humor="pun")
        assert run(engine, "That was funny") == "Your joke was funny"

    def test_it_refers_to_the_bots_favorite(self, engine):
        self.reply_and_record(engine, "What is your favorite color?")
        assert run(engine, "I like it too").startswith("I like the color ")

    def test_that_refers_to_the_bots_pick(self, engine):
        reply = self.reply_and_record(engine, "Do you like cats or dogs?")
        pick = "cats" if "cats" in reply else "dogs"
        assert run(engine, "I like that") == f"I like {pick}"

    def test_them_refers_to_plural_thing(self, engine):
        self.reply_and_record(engine, "Do you like dinosaurs?")
        assert run(engine, "Yes I love them") == "Yes I love dinosaurs"

    def test_bot_echo_does_not_replace_the_childs_event(self, engine):
        self.reply_and_record(engine, "We went to the zoo")
        assert run(engine, "That was fun") == "Going to the zoo was fun"


class TestAmbiguousPeople:
    def test_two_new_people_are_not_guessed(self, engine):
        assert run(engine, "Maya and Jake came over", "She was nice") == "She was nice"
        assert engine.references.ambiguous_options(USER) == ["Maya", "Jake"]

    def test_bot_asks_which_one(self, engine):
        resolved = run(engine, "Maya and Jake came over", "She was nice")
        reply = engine.generate_response(resolved, personality())
        assert "Maya or Jake" in reply

    @pytest.mark.parametrize("answer", ["Maya", "Maya!", "I mean Maya"])
    def test_answer_resolves_the_earlier_message(self, engine, answer):
        run(engine, "Maya and Jake came over", "She was nice")
        assert run(engine, answer) == "Maya was nice"
        assert run(engine, "He was mean") == "Jake was mean"

    def test_other_reply_clears_the_question(self, engine):
        run(engine, "Maya and Jake came over", "She was nice", "Never mind")
        assert engine.references.ambiguous_options(USER) == []

    def test_known_pronoun_is_not_ambiguous(self, engine):
        run(engine, "I played with Maya", "She was nice", "Maya and Jake came over")
        assert run(engine, "She was funny") == "Maya was funny"
