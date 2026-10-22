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
        reply = engine.generate_response("do you think so?", make_personality())
        assert reply in engine.kb["fallbacks"]["question"]

    def test_known_world_question_is_answered(self, engine):
        reply = engine.generate_response("why is the sky blue?", make_personality())
        assert reply.startswith("The sky looks blue")

    def test_unknown_world_question_suggests_looking_it_up(self, engine):
        reply = engine.generate_response("what time is it?", make_personality())
        assert reply in engine.kb["fallbacks"]["world_question"]

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


class TestOtherPeoplesFeelings:
    @pytest.mark.parametrize("message,mood", [
        ("My friend is sad", "sad"), ("Maya feels lonely", "sad"), ("My mom was really angry", "angry"),
        ("My brother is happy", "happy"), ("My friend isn't happy", "sad"),
    ])
    def test_rule_and_mood(self, engine, message, mood):
        frame = engine.analyze(message).frames[0]
        assert frame.rule_id == "other_feeling"
        assert frame.slots["emotion_mood"] == mood

    def test_reply_is_about_the_other_person(self, engine):
        reply = engine.generate_response("My friend is sad", make_personality())
        assert "your friend is sad" in reply.lower()
        assert "That sounds really hard" not in reply

    def test_negation_is_kept_in_reply(self, engine):
        reply = engine.generate_response("My friend isn't happy", make_personality())
        assert "not happy" in reply

    def test_childs_own_feeling_is_still_the_feeling_rule(self, engine):
        assert rule_ids(engine, "I am sad")[0] == "feeling"

    def test_non_emotion_state_is_still_a_person_event(self, engine):
        assert rule_ids(engine, "My dog is sick")[0] == "person_event"


class TestRequests:
    @pytest.mark.parametrize("message,rule", [
        ("Can you tell me a joke?", "request"),
        ("Tell me a joke", "request"),
        ("tell me a fun fact", "request"),
        ("Can you tell me a story?", "request"),
        ("Can we play a game?", "play_request"),
        ("Let's play a game", "play_request"),
        ("Can you help me with my homework?", "help_request"),
        ("help me", "help_request"),
        ("Can you sing?", "ability_question"),
        ("I want to tell you a joke", "offer_content"),
        ("Do you want to hear a joke?", "offer_content"),
    ])
    def test_top_rule(self, engine, message, rule):
        assert rule_ids(engine, message)[0] == rule

    @pytest.mark.parametrize("message", ["My mom told me a story", "I played a game yesterday", "She helped me"])
    def test_statements_are_not_requests(self, engine, message):
        assert not {"request", "play_request", "help_request"} & set(rule_ids(engine, message))

    def test_joke_request_tells_a_joke(self, engine):
        from services.pun_quirk_service import pun_quirk_service
        reply = engine.generate_response("Can you tell me a joke?", make_personality())
        all_puns = [p for name in dir(pun_quirk_service) if name.endswith("_PUNS")
                    for p in getattr(pun_quirk_service, name)]
        assert any(p in reply for p in all_puns)

    def test_another_one_repeats_the_last_kind(self, engine):
        from services.fact_quirk_service import fact_quirk_service
        engine.generate_response("tell me a fun fact", make_personality())
        reply = engine.generate_response("another one", make_personality())
        all_facts = [f for name in dir(fact_quirk_service) if name.endswith("_FACTS")
                     for f in getattr(fact_quirk_service, name)]
        assert any(f in reply for f in all_facts)

    def test_another_without_earlier_request_asks(self, engine):
        reply = engine.generate_response("another one", make_personality(user_id=99))
        assert reply == "Another what? A joke or a fun fact?"

    def test_offer_is_not_stored_as_goal(self, engine):
        assert memories(engine, "I want to tell you a joke") == []

    def test_help_does_not_offer_to_do_homework(self, engine):
        reply = engine.generate_response("Can you help me with my homework?", make_personality())
        assert "can't do your homework for you" in reply

    def test_requested_content_rules_skip_extra_jokes(self, engine):
        assert engine.rule_flag("request", "no_jokes")
        assert not engine.rule_flag("like_thing", "no_jokes")


class TestComparisons:
    @pytest.mark.parametrize("message,expected", [
        ("Cats are better than dogs", ("favorite", "prefers_cats_over_dogs", "cats over dogs")),
        ("Math is worse than art", ("favorite", "prefers_art_over_math", "art over math")),
        ("I like cats more than dogs", ("favorite", "prefers_cats_over_dogs", "cats over dogs")),
        ("I like chocolate ice cream better than vanilla",
         ("favorite", "prefers_chocolate_ice_cream_over_vanilla", "chocolate ice cream over vanilla")),
    ])
    def test_preference_is_remembered(self, engine, message, expected):
        found = [(c, k, v.lower()) for c, k, v in memories(engine, message)]
        assert expected in found

    def test_like_more_also_stores_the_like(self, engine):
        assert ("favorite", "likes_cats", "cats") in memories(engine, "I like cats more than dogs")

    def test_neutral_comparison_stores_nothing(self, engine):
        assert memories(engine, "Elephants are bigger than mice") == []

    @pytest.mark.parametrize("message", [
        "Is soccer better than basketball?", "Do you like cats or dogs?", "Which is better, cats or dogs?",
    ])
    def test_bot_picks_one_consistently(self, engine, message):
        frame = engine.analyze(message).frames[0]
        assert frame.rule_id == "comparison_question"
        options = {frame.slots["x"].lower(), frame.slots["y"].lower()}
        replies = [engine.generate_response(message, make_personality()).lower() for _ in range(4)]
        # Each reply names only the bot's pick, and it is the same every time
        picks = {option for option in options for reply in replies if option in reply}
        assert len(picks) == 1


class TestLongMessages:
    def test_last_clause_about_child_is_echoed(self, engine):
        reply = engine.generate_response(
            "So yesterday my brother and his friend came over and they built a huge fort in the "
            "living room and my dad got kind of mad", make_personality())
        assert "your dad got kind of mad" in reply.lower()

    def test_clause_without_subject_takes_it_from_the_joined_clause(self, engine):
        doc = engine.parser.parse(
            "Yesterday after school we went all the way across town to the giant new trampoline park and jumped for hours")
        assert engine._last_clause_about_child(doc) == "you jumped for hours"

    def test_long_message_without_known_subject_gets_no_echo(self, engine):
        doc = engine.parser.parse(
            "The thing about the new science museum downtown is that there are so many rooms full of really old stuff")
        assert engine._last_clause_about_child(doc) is None


class TestR7RuleFixes:
    def test_pronoun_object_is_not_an_achievement(self, engine):
        assert "achievement" not in rule_ids(engine, "I get it")

    def test_reflected_are_agrees_with_i(self, engine):
        reply = engine.generate_response("I think that you are tall", make_personality())
        assert "I am tall" in reply

    def test_relative_clause_i_is_not_a_coordinated_subject(self, engine):
        reply = engine.generate_response("The game that I played was fun", make_personality())
        assert "the game that you played was fun" in reply.lower()

    def test_definite_thing_subject_is_echoed(self, engine):
        reply = engine.generate_response("The tower broke", make_personality())
        assert "the tower broke" in reply.lower()


class TestReactionsToTheBot:
    def reply(self, engine, message):
        return engine.generate_response(message, make_personality())

    @pytest.mark.parametrize("message,expected", [
        ("Your name is cool", "my name"),
        ("Your fun fact is so cool", "my fun fact"),
        ("Your joke was funny", "my joke"),
        ("Your shirt looks nice", "my shirt"),
    ])
    def test_praise_of_the_bots_things_is_thanked(self, engine, message, expected):
        assert rule_ids(engine, message)[0] == "bot_thing_evaluation"
        reply = self.reply(engine, message)
        assert "thanks" in reply.lower() and expected in reply

    def test_criticism_of_the_bots_things(self, engine):
        reply = self.reply(engine, "Your name is weird")
        assert reply.startswith("You think my name is weird?")

    def test_statement_about_the_bots_name_is_not_a_question(self, engine):
        assert "bot_name_question" not in rule_ids(engine, "Your name is cool")
        assert "bot_name_question" in rule_ids(engine, "What's your name?")

    @pytest.mark.parametrize("message,expected", [
        ("That sounds fun", "sounds fun"),
        ("The movie looks boring", "the movie looks boring to you"),
    ])
    def test_sounds_and_looks(self, engine, message, expected):
        assert rule_ids(engine, message)[0] == "sounds_evaluation"
        assert expected in self.reply(engine, message).lower()

    @pytest.mark.parametrize("message", ["That's a hard question", "That's a good question", "It's a tough question"])
    def test_hard_question(self, engine, message):
        assert rule_ids(engine, message)[0] == "hard_question"
        assert "no wrong answer" in self.reply(engine, message)


class TestTranscriptFixes:
    """Replies from a reported conversation (activities, lists, pet names, "a good dog")"""

    def reply(self, engine, message):
        return engine.generate_response(message, make_personality())

    @pytest.mark.parametrize("message,reflected,key", [
        ("I like to play Minecraft.", "playing Minecraft", "likes_playing_minecraft"),
        ("I like to take the dog on walks.", "taking the dog on walks", "likes_taking_the_dog_on_walks"),
        ("I love playing soccer", "playing soccer", "likes_playing_soccer"),
    ])
    def test_activities_are_reflected_as_ing_forms(self, engine, message, reflected, key):
        assert reflected.lower() in self.reply(engine, message).lower()
        assert ("favorite", key, reflected) in memories(engine, message)

    def test_disliked_activity(self, engine):
        assert ("dislike", "dislikes_swimming", "swimming") in memories(engine, "I don't like to swim")

    def test_goal_keeps_its_infinitive(self, engine):
        assert ("goal", "goal_learn_to_swim", "learn to swim") in memories(engine, "I want to learn to swim")

    @pytest.mark.parametrize("message,expected", [
        ("I have two cats, a dog, and seven ducks.",
         [("basic", "has_cat", "two cats"), ("basic", "has_dog", "a dog"), ("basic", "has_duck", "seven ducks")]),
        ("I have a dog, a cat and a fish",
         [("basic", "has_dog", "a dog"), ("basic", "has_cat", "a cat"), ("basic", "has_fish", "a fish")]),
        ("I have a brother", [("basic", "has_brother", "a brother")]),
    ])
    def test_each_list_item_is_its_own_memory(self, engine, message, expected):
        assert memories(engine, message) == expected

    @pytest.mark.parametrize("message,name,relation", [
        ("The dog's name is Roxie.", "Roxie", "dog"),
        ("My mom's name is Sarah", "Sarah", "mom"),
        ("my dog's name is roxie", "Roxie", "dog"),
    ])
    def test_relation_name(self, engine, message, name, relation):
        assert rule_ids(engine, message)[0] == "relation_name_is"
        assert ("person", f"{relation}_{name.lower()}", name) in memories(engine, message)
        assert name in self.reply(engine, message)

    def test_someone_elses_pets_name_is_not_the_childs(self, engine):
        assert "relation_name_is" not in rule_ids(engine, "Jake's dog's name is Roxie")

    @pytest.mark.parametrize("message,expected", [
        ("Roxie is a good dog.", "Roxie is a good dog"),
        ("Roxie is not a bad dog", "Roxie is not a bad dog"),
        ("My dog is a good boy", "your dog is a good boy"),
    ])
    def test_positive_noun_evaluation(self, engine, message, expected):
        assert rule_ids(engine, message)[0] == "noun_evaluation"
        reply = self.reply(engine, message)
        assert expected.lower() in reply.lower() and "What happened" not in reply

    @pytest.mark.parametrize("message", ["Roxie is a bad dog", "Roxie is not a good dog", "Roxie isn't a nice cat"])
    def test_negative_noun_evaluation(self, engine, message):
        assert rule_ids(engine, message)[0] == "noun_evaluation"
        assert "What happened?" in self.reply(engine, message)
