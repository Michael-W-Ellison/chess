"""
Tests for the rule-based response engine
Skipped when spaCy or its English model is not installed.
"""

import random
from types import SimpleNamespace

import pytest

from services.response_engine import ResponseEngine
from services.utterance_parser import UtteranceParser

pytestmark = pytest.mark.skipif(
    not UtteranceParser().is_available(), reason="spaCy model en_core_web_sm not installed"
)


@pytest.fixture
def engine():
    return ResponseEngine(rng=random.Random(0))


def make_personality(**overrides):
    values = dict(
        id=1, user_id=1, name="Buddy", mood="happy", friendship_level=1,
        energy=0.7, curiosity=0.0, formality=0.3, get_interests=lambda: [],
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def rule_ids(engine, message):
    return [frame.rule_id for frame in engine.analyze(message).frames]


def memories(engine, message):
    return engine.extract_memories(message)


class TestRuleMatching:
    @pytest.mark.parametrize("message,rule", [
        ("hi", "greeting"),
        ("I love playing soccer", "like_thing"),
        ("i really like pizza", "like_thing"),
        ("I don't like broccoli anymore", "dislike_thing"),
        ("I hate homework", "dislike_thing"),
        ("My favorite color is blue", "favorite_is"),
        ("Soccer is my favorite sport", "favorite_is"),
        ("My best friend Maya moved away last week", "person_event"),
        ("My dog is sick", "person_event"),
        ("Jake is my brother", "person_relation"),
        ("I feel sad because my dog is sick", "feeling"),
        ("im so happy", "feeling"),
        ("I won my soccer game today", "achievement"),
        ("I failed my math test", "setback"),
        ("I want to be a scientist", "goal"),
        ("my name is Sam", "name_is"),
        ("I am 10 years old", "age_is"),
        ("What is your favorite color?", "bot_favorite_question"),
        ("Do you like dinosaurs?", "bot_like_question"),
        ("What's your name?", "bot_name_question"),
        ("How are you?", "bot_how_are_you"),
        ("thanks!", "thanks"),
        ("bye", "farewell"),
    ])
    def test_top_rule(self, engine, message, rule):
        assert rule_ids(engine, message)[0] == rule

    def test_same_structure_different_wording(self, engine):
        """One structural rule covers tense, adverbs and different objects"""
        for message in ["I like swimming", "I really loved my trip", "I enjoy reading books", "I adore cats"]:
            assert "like_thing" in rule_ids(engine, message), message

    def test_negation_is_not_a_like(self, engine):
        assert "like_thing" not in rule_ids(engine, "I don't like spiders")

    def test_feeling_requires_known_emotion(self, engine):
        assert "feeling" not in rule_ids(engine, "I am tall")

    def test_unmatched_message_has_no_frames(self, engine):
        assert rule_ids(engine, "We went to the zoo and saw a giraffe") == []


class TestMemoryExtraction:
    def test_like(self, engine):
        assert memories(engine, "I love playing soccer") == [("favorite", "likes_playing_soccer", "playing soccer")]

    def test_dislike(self, engine):
        assert memories(engine, "I don't like broccoli") == [("dislike", "dislikes_broccoli", "broccoli")]

    def test_favorite(self, engine):
        assert memories(engine, "My favorite color is blue") == [("favorite", "favorite_color", "blue")]
        [(category, key, value)] = memories(engine, "Soccer is my favorite sport")
        assert (category, key, value.lower()) == ("favorite", "favorite_sport", "soccer")

    def test_person_from_appositive_name(self, engine):
        assert ("person", "best_friend_maya", "Maya") in memories(engine, "My best friend Maya moved away")

    def test_person_from_copula(self, engine):
        assert memories(engine, "Jake is my brother") == [("person", "brother_jake", "Jake")]

    def test_goal(self, engine):
        assert memories(engine, "I want to be a scientist") == [("goal", "goal_be_a_scientist", "be a scientist")]

    def test_achievement_is_stored_from_bot_perspective_without_date(self, engine):
        assert memories(engine, "I won my soccer game today") == [
            ("achievement", "achievement_won_my_soccer_game", "won your soccer game")
        ]

    def test_name_and_age(self, engine):
        assert memories(engine, "my name is sam") == [("basic", "name", "Sam")]
        assert memories(engine, "I am 10 years old") == [("basic", "age", "10")]

    def test_people_are_not_stored_as_likes(self, engine):
        assert memories(engine, "I love my dog") == []
        assert rule_ids(engine, "I love my dog") == ["love_person"]

    def test_child_spellings_are_normalized(self, engine):
        assert memories(engine, "i luv swimming") == [("favorite", "likes_swimming", "swimming")]


class TestMood:
    @pytest.mark.parametrize("message,mood", [
        ("I feel sad because my dog is sick", "sad"),
        ("I'm so happy", "happy"),
        ("I am worried about my test", "anxious"),
        ("I'm unhappy", "sad"),
        ("My best friend moved away", "sad"),
    ])
    def test_detected_mood(self, engine, message, mood):
        assert engine.detect_mood(message) == mood

    def test_no_mood(self, engine):
        assert engine.detect_mood("I like pizza") is None


class TestResponses:
    def test_perspective_is_swapped(self, engine):
        reply = engine.generate_response("I won my soccer game today", make_personality())
        assert "You won your soccer game today?" in reply

    def test_reason_clause_is_used(self, engine):
        reply = engine.generate_response("I feel sad because my dog is sick", make_personality())
        assert "your dog is sick" in reply
        assert "because because" not in reply

    def test_bot_answers_its_name(self, engine):
        reply = engine.generate_response("What's your name?", make_personality(name="Pip"))
        assert "Pip" in reply

    def test_bot_favorite_is_stable(self, engine):
        personality = make_personality()
        favorites = set()
        for _ in range(6):
            reply = engine.generate_response("What is your favorite color?", personality)
            favorites.update(c for c in engine.kb["bot_profile"]["favorites"]["color"] if c in reply)
        assert len(favorites) == 1

    def test_unknown_question_gets_question_fallback(self, engine):
        reply = engine.generate_response("why is the sky blue?", make_personality())
        assert reply in engine.kb["fallbacks"]["question"]

    def test_reflection_fallback(self, engine):
        reply = engine.generate_response("We went to the zoo and saw a giraffe", make_personality())
        assert "you went to the zoo and saw a giraffe" in reply.lower()

    def test_reflection_can_be_disabled(self, engine):
        """Used when the safety filter flagged the message: the child's words are not echoed"""
        for message in ["We went to the zoo", "My best friend Maya moved away", "the stupid movie"]:
            reply = engine.generate_response(message, make_personality(), allow_reflection=False)
            assert "zoo" not in reply and "Maya" not in reply and "stupid" not in reply

    def test_user_name_in_greeting(self, engine):
        assert "Sam" in engine.generate_response("hello", make_personality(), user_name="Sam")


class TestPersonalityShaping:
    def test_low_energy_has_no_exclamations(self, engine):
        reply = engine.generate_response("I won my soccer game today", make_personality(energy=0.1))
        assert "!" not in reply

    def test_high_formality_substitutes_wording(self, engine):
        personality = make_personality(formality=0.9)
        replies = [engine.generate_response("I won my soccer game today", personality) for _ in range(6)]
        assert not any("awesome" in r or "That's" in r for r in replies)

    def test_curiosity_controls_follow_up_questions(self, engine):
        curious = make_personality(curiosity=1.0)
        incurious = make_personality(curiosity=0.0)
        follow_ups = engine.rules["achievement"]["follow_ups"]
        assert any(f in engine.generate_response("I won my game", curious) for f in follow_ups)
        assert not any(f in engine.generate_response("I won my game", incurious) for f in follow_ups)

    def test_memory_callback_needs_friendship_level_3(self, engine):
        remembered = [SimpleNamespace(category="goal", key="goal_x", value="be a scientist")]
        engine.rng = random.Random(0)
        low = [engine.generate_response("thanks", make_personality(friendship_level=1),
                                        {"relevant_memories": remembered}) for _ in range(20)]
        high = [engine.generate_response("thanks", make_personality(friendship_level=4),
                                         {"relevant_memories": remembered}) for _ in range(20)]
        assert not any("scientist" in r for r in low)
        assert any("scientist" in r for r in high)

    def test_does_not_repeat_the_same_template_twice_in_a_row(self, engine):
        replies = [engine.generate_response("We went to the park", make_personality()) for _ in range(10)]
        assert all(a != b for a, b in zip(replies, replies[1:]))


class TestSchoolAndDay:
    @pytest.mark.parametrize("message,rule", [
        ("I have a math test tomorrow", "school_upcoming"),
        ("We have a big project due Friday", "school_upcoming"),
        ("I got a bad grade", "bad_result"),
        ("I got an F", "bad_result"),
        ("I got in trouble at school", "bad_result"),
        ("I got an A on my spelling test", "achievement"),
        ("I made the soccer team", "achievement"),
        ("School was boring", "evaluation"),
        ("My day was good", "evaluation"),
        ("good", "short_answer"),
        ("not bad", "short_answer"),
        ("nothing much", "nothing_much"),
        ("What did you do today?", "bot_day_question"),
        ("We're going to the beach tomorrow", "plan"),
    ])
    def test_top_rule(self, engine, message, rule):
        assert rule_ids(engine, message)[0] == rule

    def test_bad_grade_is_not_an_achievement(self, engine):
        assert "achievement" not in rule_ids(engine, "I got a bad grade")
        assert memories(engine, "I got a bad grade") == []

    def test_upcoming_test_reply(self, engine):
        reply = engine.generate_response("I have a math test tomorrow", make_personality())
        assert "you have a math test tomorrow" in reply.lower()

    def test_evaluation_keeps_negation(self, engine):
        reply = engine.generate_response("It was not fun", make_personality())
        assert "not fun" in reply

    @pytest.mark.parametrize("message,valence", [
        ("good", "positive"), ("pretty good", "positive"), ("not bad", "positive"),
        ("awful", "negative"), ("not fun", "negative"), ("okay", "neutral"),
    ])
    def test_short_answer_valence(self, engine, message, valence):
        frame = engine.analyze(message).frames[0]
        assert frame.slots["evaluation_valence"] == valence

    def test_common_noun_subject_is_lowercased(self, engine):
        reply = engine.generate_response("School was boring", make_personality())
        assert "school was boring" in reply.lower() and "School was" not in reply[1:]


class TestPeople:
    @pytest.mark.parametrize("message,rule", [
        ("My teacher yelled at me", "person_upset"),
        ("My mom grounded me", "person_upset"),
        ("My dad bought me a puppy", "person_kindness"),
        ("My grandma taught me how to knit", "person_kindness"),
        ("Maya was nice", "person_evaluation"),
        ("My brother is annoying", "person_evaluation"),
        ("I have a dog named Max", "have_named"),
        ("I have two sisters", "have_relation"),
    ])
    def test_top_rule(self, engine, message, rule):
        assert rule_ids(engine, message)[0] == rule

    def test_reply_reflects_object_pronoun(self, engine):
        reply = engine.generate_response("My teacher yelled at me", make_personality())
        assert "your teacher yelled at you" in reply.lower()

    def test_named_pet_is_remembered(self, engine):
        assert memories(engine, "I have a dog named Max") == [("person", "dog_max", "Max")]

    def test_siblings_are_remembered(self, engine):
        assert memories(engine, "I have two sisters") == [("basic", "has_sister", "two sisters")]

    def test_person_evaluation_does_not_ask_for_best_part(self, engine):
        reply = engine.generate_response("Maya was nice", make_personality())
        assert "best part" not in reply


class TestFeelingsAndBot:
    @pytest.mark.parametrize("message", ["I cried today", "I'm going to cry", "I feel like crying", "I want to cry"])
    def test_crying_sets_sad_mood(self, engine, message):
        analysis = engine.analyze(message)
        assert analysis.frames[0].rule_id == "crying"
        assert analysis.mood == "sad"

    def test_crying_is_not_a_goal(self, engine):
        assert memories(engine, "I want to cry") == []

    def test_bored_reply_suggests_something_to_do(self, engine):
        reply = engine.generate_response("I'm bored", make_personality())
        assert reply in [v["text"].replace("{emotion}", "bored")
                         for v in engine.rules["feeling"]["responses_by"]["variants"]["bored"]]

    @pytest.mark.parametrize("message", ["Are you a robot?", "Are you real?", "are you a human?"])
    def test_bot_says_it_is_not_a_person(self, engine, message):
        reply = engine.generate_response(message, make_personality())
        assert "not a real person" in reply or "not a human" in reply


class TestMultiSentenceAndWordOrder:
    def test_two_sentences_get_two_answers_in_order(self, engine):
        reply = engine.generate_response("I won my game today! Do you like soccer?", make_personality())
        assert "You won your game today?" in reply
        assert "soccer" in reply.lower()
        assert reply.index("won your game") < reply.lower().index("soccer")

    def test_question_in_one_sentence_does_not_block_rules_in_another(self, engine):
        assert "achievement" in rule_ids(engine, "I won my game today! Do you like soccer?")

    def test_greeting_is_not_added_as_second_answer(self, engine):
        reply = engine.generate_response("Hi! I made the soccer team", make_personality())
        assert "made the soccer team" in reply
        assert "What's up" not in reply and "How's your day" not in reply

    def test_reflection_uses_last_reflectable_sentence(self, engine):
        reply = engine.generate_response("Guess what. We went to the zoo", make_personality())
        assert "you went to the zoo" in reply.lower()

    @pytest.mark.parametrize("message,expected", [
        ("My mom and I baked cookies", "you and your mom baked cookies"),
        ("Me and my brother played video games", "you and your brother played video games"),
        ("Sam and I built a fort", "you and sam built a fort"),
        ("My mom, my dad and I went camping", "you, your mom and your dad went camping"),
    ])
    def test_coordinated_subject_word_order(self, engine, message, expected):
        reply = engine.generate_response(message, make_personality())
        assert expected in reply.lower()

    def test_inner_punctuation_keeps_spacing(self, engine):
        reply = engine.generate_response("Um, I went to the store, the park and home", make_personality())
        assert "the store, the park and home" in reply
