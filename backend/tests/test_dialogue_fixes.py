"""
Replies found wrong in scripted child conversations: names, pets, tenses, sad news,
questions to the bot, short answers and slang.
Skipped when spaCy or its English model is not installed.
"""

import itertools
import logging
import random
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from main import app
from services.emoji_quirk_service import emoji_quirk_service
from services import response_engine as engine_module
from services.response_engine import ResponseEngine
from services.safety_filter import safety_filter
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


def rule_of(engine, message, user_id=1):
    """The rule (or fallback) the engine used to reply, after resolving references"""
    features = {}
    resolved = engine.resolve_references(message, user_id)
    reply = engine.generate_response(resolved, make_personality(user_id=user_id), features=features)
    engine.record_bot_reply(user_id, reply or "")
    return features.get("rule"), reply


class TestNewRules:
    @pytest.mark.parametrize("message,rule", [
        ("I miss my grandpa", "miss_person"),
        ("my grandma is feeling better", "person_better"),
        ("can you give me advice", "ask_for_advice"),
        ("what if nobody likes me", "what_if_liked"),
        ("what if no one wants to play with me", "what_if_liked"),
        ("what if I fail the test", "what_if_worry"),
        ("my mom said we can get a new one", "get_new_later"),
        ("I don't want a new one", "not_want_new"),
        ("I got a new bike", "got_gift"),
        ("what if it rains", "what_if_weather"),
        ("what if the sun disappeared", "what_if_question"),
        ("my brother knocked the snowman over", "wrecked_my_thing"),
        ("jake broke my pencil", "wrecked_my_thing"),
        ("i cant sleep", "cant_sleep"),
        ("goodnight", "goodnight"),
        ("good night", "goodnight"),
        ("but also kind of nervous", "feeling_fragment"),
        ("what if they forget about me", "what_if_forgotten"),
        ("we called him biscuit", "name_someone"),
        ("what game do you like", "bot_like_which"),
        ("why did the chicken cross the road", "child_joke"),
        ("knock knock", "child_joke"),
        ("do you like farts", "bot_like_gross"),
        ("my parents are getting divorced", "parents_divorce"),
        ("my mom and dad are splitting up", "parents_divorce"),
        ("will they still love me", "still_love_me"),
        ("can i tell you a secret", "tell_secret"),
        ("dont tell anyone", "dont_tell"),
        ("i like a boy in my class", "crush_boy"),
        ("he has to go home now", "other_goes_home"),
        ("i have to go", "gotta_go"),
        ("whats brown and sticky", "child_joke"),
        ("tell me another", "request_again_tell"),
        ("i looked everywhere", "looked_everywhere"),
        ("their names are luna and milo", "names_are"),
        ("it rained all night", "weather_past"),
        ("its raining", "weather"),
        ("i told him to stop", "told_to_stop"),
        ("he didnt stop", "didnt_stop"),
        ("she said to ignore him", "advice_ignore"),
        ("i already did that", "already_did"),
        ("ok what else", "what_else"),
        ("did you know sharks dont have bones", "did_you_know"),
        ("how do you spell because", "spelling"),
        ("coach said I did great", "praise_reported"),
        ("not much you", "not_much"),
        ("yes", "yes_no"),
        ("I guess", "yes_no"),
        ("it's not fair", "not_fair"),
        ("what's up", "whats_up"),
        ("guess what", "guess_what"),
        ("wow", "wow"),
        ("lol", "laugh"),
        ("I don't know", "dont_know"),
        ("I don't know anyone", "know_nobody"),
        ("I don't know how to start", "dont_know_how"),
        ("I have a fever", "sick"),
        ("my tummy hurts", "body_hurts"),
        ("I don't feel good", "not_feel_good"),
        ("my friend said she doesn't want to be my friend anymore", "unfriended"),
        ("nobody plays with me at recess", "left_out"),
        ("my brother says I'm annoying", "person_says_about_me"),
        ("my brother always takes my stuff", "takes_my_stuff"),
        ("I'll try that", "will_try"),
        ("what ride should I go on", "which_should_i"),
        ("have you been there", "bot_been_question"),
        ("have you ever had sushi", "bot_been_question"),
        ("you're funny", "bot_compliment"),
        ("how old are you", "bot_age_question"),
        ("where do you live", "bot_home_question"),
        ("do you have friends", "bot_friends_question"),
        ("what food do you hate", "bot_dislike_question"),
        ("I'm turning 11", "age_short"),
        ("tomorrow is my birthday!", "birthday"),
        ("I learned to ride my bike!", "achievement"),
        ("but I kept trying", "kept_trying"),
        ("now I can ride all by myself", "can_now"),
        ("I have so much homework", "lots_of_homework"),
        ("I don't want to talk about it", "dont_want_to_talk"),
        ("can we talk about something else", "change_subject"),
        ("the dog is named Buster", "relation_named"),
        ("the dragon is named Sparky", "thing_named"),
        ("maybe we can be friends", "could_be_friends"),
        ("got to go bye", "gotta_go"),
        ("just kidding", "just_kidding"),
        ("ok bye", "farewell_last"),
        ("bye", "farewell"),
        ("everyone was mad at me", "everyone_mad"),
        ("how do I get better at soccer", "get_better"),
        ("I hope he likes me", "hope"),
        ("what should we name him", "naming_question"),
        ("my mom is having a baby", "new_baby"),
        ("it's a boy", "baby_gender"),
        ("what color do you like", "bot_like_which"),
        ("what do you like to do", "bot_hobby_question"),
        ("do you get bored", "bot_feeling_question"),
        ("a kid hit me with the ball", "hit_by_ball"),
        ("it didn't hurt", "didnt_hurt"),
        ("we won", "we_won"),
        ("I had a bad dream", "bad_dream"),
        ("can you make me feel better", "cheer_me_up"),
        ("it was an accident", "accident"),
        ("should I say sorry", "should_apologize"),
        ("can you tell me something funny", "request_funny"),
        ("my cat bit me", "pet_bite"),
        ("at soccer a boy pushed me", "pushed_me"),
        ("I fell and scraped my knee", "got_hurt"),
        ("what if I fail", "what_if_worry"),
        ("I don't know what to do", "dont_know_what"),
        ("I lost a tooth today", "lost_tooth"),
        ("my best friend said I was mean", "person_says_about_me"),
        ("my mom said I did a good job", "praise_reported"),
        ("my grandma is really good at cards", "good_at"),
        ("I'm bad at spelling", "good_at"),
        ("I'm good", "feeling"),
        ("can I get a new fish", "ask_permission"),
        ("are you a boy or a girl", "bot_gender_question"),
        ("do you have a family", "bot_family_question"),
        ("will you still talk to me", "bot_still_here"),
        ("my mom took away my ipad", "taken_away"),
        ("ugh", "ugh"),
        ("I hit the target", "hit_target"),
        ("I made a new friend named Leo", "new_friend"),
        ("we are moving to a new house", "moving_house"),
        ("do you like cupcakes", "bot_like_food"),
        ("why is the sky blue", "fallback_world_answer"),
        ("how far is the moon", "fallback_world_answer"),
        ("do you know about planets", "fallback_world_question_fact"),
        ("what time is it", "fallback_world_question"),
        ("why do penguins not fly", "fallback_world_answer"),
        ("nobody picked me for their team", "left_out"),
        ("its raining", "weather"),
        ("what can I do inside", "bored_ideas"),
        ("should I start over", "should_i"),
        ("my favorite was the penguins", "favorite_bare"),
        ("we can't go to the park", "fallback_reflection_cant"),
        ("the giraffe was so tall", "fallback_reflection_be"),
        ("today was the best day ever", "day_evaluation"),
        ("today was the worst day", "day_evaluation"),
        ("I just want to go home", "want_to_go_home"),
        ("I really want a dog", "want_thing"),
        ("my parents said no", "said_no"),
        ("what kind of dog should I get", "which_should_i"),
        ("do you think I was good enough", "do_you_think_i"),
        ("do you think I can beat her", "do_you_think_i"),
        ("it made me feel sad", "made_me_feel"),
        ("that stinks", "that_stinks"),
        ("what do you want for christmas", "bot_want_question"),
        ("I want to be a vet", "goal"),
        ("my sister is really good", "person_evaluation"),
        ("my sister is sad", "other_feeling"),
        ("there was a shark", "there_was"),
        ("can we go again", "ask_permission"),
        ("it was my first goal ever", "first_ever"),
        ("will my friend be ok", "will_be_ok"),
        ("I get allowance", "allowance"),
        ("is a whale a fish", "fallback_world_answer"),
        ("The starfish felt bumpy", "fallback_reflection_be"),
        ("I have 20 dinosaur toys", "have_many"),
        ("I got a c on my test", "grade"),
        ("my dad was disappointed", "other_feeling"),
        ("I studied really hard", "tried_hard"),
        ("I feel stupid", "feel_stupid"),
        ("I feel bad", "feeling"),
        ("is it scary", "is_it_scary"),
        ("guess what I had for breakfast", "guess_what_i"),
        ("pancakes", "food_mention"),
        ("sing me a song", "bot_song"),
        ("ok bye buddy", "farewell_last"),
        ("school is cancelled", "school_cancelled"),
        ("a big dog barked at me", "animal_scary"),
        ("it made me scared", "made_me_feel"),
        ("I want to buy a toy", "want_to_buy"),
        ("I made 12 dollars", "allowance"),
        ("I got a goody bag", "got_gift"),
        ("I got a B", "achievement"),
        ("do you have a brain", "bot_body_question"),
        ("do you have feelings", "bot_body_question"),
        ("can you think", "bot_think_question"),
        ("can you remember my name", "ask_my_name"),
        ("the snowman's name is Frosty", "thing_name_is"),
        ("how do computers work", "fallback_world_answer"),
        ("we found him", "found_it"),
        ("I didn't have any cavities", "no_cavities"),
        ("I got a new toothbrush", "got_gift"),
        ("I feel left out", "feel_left_out"),
        ("when will I get one", "will_i"),
        ("I didn't want to leave", "didnt_want_to_leave"),
        ("if you could be any animal what would you be", "bot_would_be"),
        ("what is half of 10", "arithmetic"),
        ("what is a fraction", "fallback_world_answer"),
        ("my aunt had a baby", "new_baby"),
        ("I got to hold my baby cousin", "got_to"),
        ("I don't have one", "fallback_reflection_cant"),
        ("can we make up a story", "story_together"),
        ("why", "why_alone"),
        ("😂", "laugh"),
        ("😭", "feeling"),
        ("❤️", "aww"),
        ("I love it", "love_it"),
        ("do you like pizza or tacos", "comparison_question"),
        ("what's my name", "ask_my_name"),
        ("what is my favorite color", "ask_my_favorite"),
        ("do you remember my dog", "ask_remember"),
        ("you're dumb", "bot_compliment"),
        ("shut up", "shut_up"),
        ("I hate you", "hate_you"),
        ("sorry", "sorry"),
        ("what", "what_alone"),
        ("who made you", "bot_creator"),
        ("are you chatgpt", "bot_other_ai"),
        ("what can you do", "bot_abilities"),
        ("what color would your horse be", "bot_would_pick"),
        ("my teacher said I was brave", "person_says_about_me"),
    ])
    def test_rule(self, engine, message, rule):
        assert rule_of(engine, message)[0] == rule

    def test_arithmetic(self, engine):
        rule, reply = rule_of(engine, "what's 2 plus 2")
        assert rule == "arithmetic"
        assert reply.startswith("2 plus 2 is 4!")

    def test_birthday_today_and_upcoming(self, engine):
        assert "Happy birthday" in rule_of(engine, "today is my birthday")[1]
        assert "coming up" in rule_of(engine, "my birthday is tomorrow")[1]

    def test_what_s_yours_answers_the_last_favorite_category(self, engine):
        rule_of(engine, "My favorite color is purple")
        rule, reply = rule_of(engine, "What's yours?")
        assert rule == "reciprocal"
        assert reply.startswith("My favorite color is")

    def test_school_task_in_the_past_is_not_upcoming(self, engine):
        assert rule_of(engine, "I had a math test today")[0] != "school_upcoming"

    def test_pet_age_in_the_past(self, engine):
        rule_of(engine, "I have a dog named Rocky")
        rule, reply = rule_of(engine, "he was 12")
        assert rule == "person_age_past"
        assert "do together" not in reply


class TestReflectionTense:
    @pytest.mark.parametrize("message,kind", [
        ("I had a math test today", "fallback_reflection"),
        ("we're going to have a party", "fallback_reflection_future"),
        ("my friends are coming over tomorrow", "fallback_reflection_future"),
        ("I'm teaching my dog to sit", "fallback_reflection_present"),
        ("my grandpa is in the hospital", "fallback_reflection_sad"),
        ("the castle is really big", "fallback_reflection_be"),
    ])
    def test_follow_up_fits_the_tense(self, engine, message, kind):
        assert rule_of(engine, message)[0] == kind

    def test_negated_sad_word_is_not_sad(self, engine):
        assert rule_of(engine, "I wasn't scared")[0] != "fallback_reflection_sad"

    def test_gentle_reflection_after_sad_news(self, engine):
        features = {}
        reply = engine.generate_response("I made him a card", make_personality(), {"sensitive": True},
                                         features=features)
        assert features["rule"] == "fallback_reflection_gentle"
        assert "What happened next" not in reply

    def test_reported_future(self, engine):
        assert rule_of(engine, "my mom said she will talk to him")[0] == "fallback_reflection_future"


class TestReferences:
    def test_new_pet_is_his(self, engine):
        rule_of(engine, "I got a new puppy!")
        assert engine.resolve_references("his name is Max", 1) == "My puppy's name is Max"
        assert engine.resolve_references("he is so cute", 1) == "My puppy Max is so cute"

    def test_pet_named_with_is_named(self, engine):
        rule_of(engine, "we have two cats and a dog")
        rule_of(engine, "the dog is named Buster")
        assert engine.resolve_references("he is really old", 1) == "My dog Buster is really old"

    def test_pet_named_in_the_same_sentence(self, engine):
        rule_of(engine, "I have a dog named max")
        assert engine.resolve_references("he is brown", 1) == "My dog Max is brown"

    def test_named_snowman(self, engine):
        rule_of(engine, "I made a snowman named frosty")
        assert engine.resolve_references("he has a carrot nose", 1) == "Frosty has a carrot nose"

    def test_possessive_of_the_clause_subject(self, engine):
        rule_of(engine, "I made a snowman named frosty")
        assert "Frosty" not in engine.resolve_references("my brother broke his arm", 1)

    def test_wrecked_by_a_name_is_capitalized(self, engine):
        _, reply = rule_of(engine, "jake broke my pencil")
        assert "Did Jake" in reply

    def test_wind_is_not_a_person_wrecking_things(self, engine):
        assert rule_of(engine, "the wind knocked the tree over")[0] != "wrecked_my_thing"

    def test_it_after_something_made_for_the_child(self, engine):
        rule_of(engine, "my throat hurts")
        rule_of(engine, "my dad made me soup")
        assert engine.resolve_references("it was yummy", 1) == "The soup was yummy"
        assert rule_of(engine, "it was yummy")[1].startswith("Yay, the soup")

    def test_school_subject_keeps_no_article(self, engine):
        rule_of(engine, "we had math")
        assert engine.resolve_references("it was boring", 1) == "Math was boring"

    def test_naming_the_new_baby(self, engine):
        rule_of(engine, "my mom is having a baby")
        assert rule_of(engine, "i want to name her lily") == (
            "name_someone", "Lily is a great name! What made you think of it?")

    def test_lowercase_friend_name_is_capitalized(self, engine):
        assert "your friend Sam" in rule_of(engine, "my friend sam helped me")[1]
        assert "Group" not in rule_of(engine, "my friend group is big")[1]
        assert "friend Lucas" in rule_of(engine, "my friend lucas came over")[1]

    def test_riddle_waits_for_a_guess(self, engine):
        riddle = rule_of(engine, "can you tell me a riddle")[1]
        assert riddle.endswith("Take a guess!")
        assert rule_of(engine, "you're funny")[0] == "bot_compliment"  # not a guess
        rule, reply = rule_of(engine, "i dont know")
        assert rule == "riddle_answer" and "The answer is" in reply and reply.endswith("Want another one?")
        rule, reply = rule_of(engine, "yes")
        assert rule == "joke_offer_yes" and reply.endswith("Take a guess!") and riddle.split(": ")[1] not in reply

    def test_yes_to_a_joke_offer(self, engine):
        rule_of(engine, "do you like farts")
        assert rule_of(engine, "yes")[1].startswith("Okay, here's one:")

    def test_creature_in_a_drawing(self, engine):
        for message in ("i drew a picture", "its a unicorn"):
            rule_of(engine, message)
        assert engine.resolve_references("she has a rainbow mane", 1) == "The unicorn has a rainbow mane"
        assert engine.resolve_references("i gave it to my grandma", 1) == "I gave the picture to my grandma"

    def test_kindness_follow_up_names_the_person(self, engine):
        rule = engine.rules["person_kindness"]
        assert "I bet {person} really care{person_s} about you!" in rule["follow_ups"]

    def test_food_that_was_had_takes_the(self, engine):
        rule_of(engine, "then we had pizza")
        assert engine.resolve_references("it was so good", 1) == "The pizza was so good"

    def test_present_is_a_thing(self, engine):
        rule_of(engine, "my grandpa brought me a present")
        assert engine.resolve_references("it was a book about sharks", 1) == "The present was a book about sharks"

    def test_plural_pets_names(self, engine):
        rule_of(engine, "i have two cats")
        assert engine.resolve_references("their names are luna and milo", 1) == "My cats' names are Luna and Milo"
        rule_of(engine, "their names are luna and milo")
        assert "Milo is" in rule_of(engine, "milo is orange")[1]

    def test_it_after_asking_who_is_not_a_name(self, engine):
        for message in ("i have two cats", "their names are luna and milo", "he scratched me"):
            rule_of(engine, message)
        assert "Milo hurt" not in rule_of(engine, "it hurt a little")[1]

    def test_choosing_from_the_offer(self, engine):
        rule_of(engine, "ok what else")
        rule, reply = rule_of(engine, "a riddle")
        assert rule == "joke_offer_yes" and reply.endswith("Take a guess!")

    def test_spelling_only_real_words(self, engine):
        assert rule_of(engine, "how do you spell asdfgh")[0] != "spelling"

    def test_did_you_know_with_a_known_answer(self, engine):
        assert rule_of(engine, "did you know how the knight moves")[0] == "fallback_world_answer"

    def test_knock_knock_joke(self, engine):
        assert rule_of(engine, "knock knock")[1] == "Who's there?"
        assert rule_of(engine, "boo")[1] == "Boo who?"
        assert rule_of(engine, "dont cry its just a joke")[0] == "child_joke"

    def test_opening_word_is_not_echoed(self, engine):
        _, reply = rule_of(engine, "fine ill eat broccoli")
        assert "fine" not in reply.lower()

    def test_teacher_with_title(self, engine):
        rule_of(engine, "my teacher is mrs garcia")
        assert engine.resolve_references("shes really nice", 1) == "My teacher Mrs Garcia is really nice"

    def test_answer_to_favorite_question(self, engine):
        engine.record_bot_reply(1, "Ooh, I love red pandas! What's your favorite animal?")
        assert engine.resolve_references("mine is a wolf", 1) == "My favorite animal is a wolf"
        engine.record_bot_reply(1, "My favorite food is pancakes! What's yours?")
        assert engine.resolve_references("sushi", 1) == "My favorite food is sushi"

    def test_answer_after_a_word_like_cool(self, engine):
        engine.record_bot_reply(1, "I love green! What color do you like?")
        assert engine.resolve_references("cool mine is green", 1) == "My favorite color is green"

    def test_bot_question_words_are_not_things(self, engine):
        engine.record_bot_reply(1, "Nice to meet you, Grace! What do you like to do for fun?")
        assert engine.resolve_references("it's a boy", 1) == "it's a boy"
        engine.reset_references(1)
        engine.record_bot_reply(1, "You lost? I'm sorry, that's no fun.")
        assert engine.resolve_references("it was 3 to 1", 1) == "it was 3 to 1"

    def test_a_boy_is_not_a_name(self, engine):
        assert ("basic", "name", "Boy") not in engine.extract_memories("My name is a boy")

    def test_added_fact_is_not_it_after_the_child_named_a_thing(self, engine):
        rule_of(engine, "I made a painting")
        engine.references.record_bot_reply(1, "You made a painting?", told="fun fact", told_was_added=True)
        assert engine.resolve_references("my teacher put it on the wall", 1) == "my teacher put the painting on the wall"

    def test_bot_filler_words_are_not_things(self, engine):
        rule_of(engine, "I hate math")
        engine.record_bot_reply(1, "Not a fan of math, huh? That's okay, everybody likes different stuff.")
        assert engine.resolve_references("its so boring", 1) == "Math is so boring"

    def test_childs_topic_over_the_bots_answer(self, engine):
        rule_of(engine, "my favorite planet is saturn")
        assert "Jupiter" not in engine.resolve_references("it has rings", 1)  # the bot's favorite

    def test_plural_thing_as_subject_gets_the(self, engine):
        rule_of(engine, "me and my dad made cupcakes")
        assert engine.resolve_references("they had sprinkles", 1) == "The cupcakes had sprinkles"

    def test_new_friend_name_is_used(self, engine):
        assert "Leo" in rule_of(engine, "I made a new friend named Leo")[1]

    def test_song_title_keeps_all_words(self, engine):
        assert "Fur elise" in rule_of(engine, "my song is called fur elise")[1]

    def test_last_one_is_not_an_age(self, engine):
        assert rule_of(engine, "I was the last one")[0] != "age_short"

    def test_singular_and_plural_food(self, engine):
        assert "cheese sounds yummy" in rule_of(engine, "do you like cheese")[1]
        assert "cupcakes sound yummy" in rule_of(engine, "do you like cupcakes")[1]

    def test_bleeding_is_the_body_part(self, engine):
        rule_of(engine, "I hurt my arm")
        engine.resolve_references("my mom put a bandaid on it", 1)
        assert engine.resolve_references("it stopped bleeding", 1) == "My arm stopped bleeding"

    def test_grown_up_from_bot_reply_is_not_it(self, engine):
        rule_of(engine, "I hurt my arm")
        engine.record_bot_reply(1, "Ouch! Have you told a grown-up?")
        assert "grown" not in engine.resolve_references("my mom put a bandaid on it", 1)

    def test_another_one_inside_a_sentence_is_not_a_request(self, engine):
        assert rule_of(engine, "I built another one")[0] != "request_again"

    def test_book_title_is_not_people(self, engine):
        rule_of(engine, "im reading harry potter")
        rule_of(engine, "my favorite character is hermione")
        assert engine.resolve_references("she is really smart", 1) == "Hermione is really smart"

    def test_added_joke_is_not_it_without_a_reaction(self, engine):
        rule_of(engine, "I built another one")
        engine.references.record_bot_reply(1, "You built another one? That's awesome!", told="joke",
                                           told_was_added=True)
        assert "joke" not in engine.resolve_references("it was even bigger", 1)

    @pytest.mark.parametrize("message,echo", [
        ("The cupcakes had sprinkles", "the cupcakes had sprinkles?"),
        ("the pizza had pepperoni", "the pizza had pepperoni?"),
    ])
    def test_had_as_main_verb_is_reflected(self, engine, message, echo):
        rule, reply = rule_of(engine, message)
        assert rule == "fallback_reflection_be"
        assert echo in reply.lower()

    def test_had_as_helper_verb_is_unchanged(self):
        doc = UtteranceParser().parse("I had eaten lunch")
        assert doc[2].dep_ == "ROOT" and doc[1].dep_ == "aux"

    def test_another_one_is_the_new_thing(self, engine):
        rule_of(engine, "I built a sandcastle")
        rule_of(engine, "I built another one")
        assert engine.resolve_references("it was even bigger", 1) == "The new sandcastle was even bigger"

    def test_child_tells_a_joke(self, engine):
        rule_of(engine, "I have a joke for you")
        rule, reply = rule_of(engine, "why did the chicken cross the road")
        assert rule == "child_joke"
        assert reply in engine_module.CHILD_JOKE_GUESSES
        rule, reply = rule_of(engine, "to get to the other side")
        assert rule == "child_joke"
        assert rule_of(engine, "why is the sky blue")[0] == "fallback_world_answer"  # back to normal

    def test_no_joke_after_a_world_answer(self, engine):
        assert engine.rule_flag("fallback_world_answer", "no_jokes")

    def test_mine_is_my_last_thing(self, engine):
        rule_of(engine, "in art we made clay pots")
        assert engine.resolve_references("mine was blue and green", 1) == "My clay pot was blue and green"

    def test_will_he_be_ok_is_not_an_evaluation(self, engine):
        assert rule_of(engine, "will my friend be nice")[0] != "person_evaluation"

    @pytest.mark.parametrize("message,text", [
        ("I love dinosaurs", "dinosaurs sound like"),
        ("I love origami", "origami sounds like"),
    ])
    def test_plural_agreement_in_templates(self, engine, message, text):
        replies = {engine.generate_response(message, make_personality(user_id=n)) for n in range(1, 12)}
        assert any(text in r.lower() for r in replies)
        assert not any(("dinosaurs sounds" in r.lower() or "origami sound " in r.lower()) for r in replies)

    def test_his_name_for_a_thing_the_child_made(self, engine):
        rule_of(engine, "we built a snowman")
        assert engine.resolve_references("his name is frosty", 1) == "The snowman's name is frosty"
        assert engine.resolve_references("he has a carrot nose", 1) == "Frosty has a carrot nose"

    def test_the_best_is_not_a_reaction_to_an_added_joke(self, engine):
        rule_of(engine, "I got a goody bag")
        engine.references.record_bot_reply(1, "Ooh, a goody bag! What was in it?", told="joke", told_was_added=True)
        assert "joke" not in engine.resolve_references("it was the best", 1)

    def test_aunts_baby_is_a_cousin(self, engine):
        assert "cousin" in rule_of(engine, "my aunt had a baby")[1]
        assert engine.resolve_references("she is so tiny", 1) == "My baby cousin is so tiny"
        engine.resolve_references("her name is rose", 1)
        assert engine.resolve_references("I got to hold her", 1) == "I got to hold my baby cousin Rose"

    def test_toy_with_a_title_name(self, engine):
        rule_of(engine, "I lost my favorite stuffed animal")
        rule, reply = rule_of(engine, "his name is mr bear")
        assert reply == "Mr Bear is a great name for an animal!"
        assert engine.resolve_references("I can't find him", 1) == "I can't find Mr Bear"

    def test_it_was_far_away(self, engine):
        rule_of(engine, "I saw a bear")
        assert engine.resolve_references("it was far away", 1) == "The bear was far away"

    def test_an_before_a_vowel(self, engine):
        assert "an animal" in rule_of(engine, "the animal's name is Mr Bear")[1]

    def test_story_together(self, engine):
        rule_of(engine, "can we make up a story")
        assert rule_of(engine, "once upon a time there was a dragon")[0] == "story"
        assert rule_of(engine, "he was lonely")[0] == "story"
        rule, reply = rule_of(engine, "the end")
        assert rule == "story" and reply in engine_module.STORY_ENDINGS
        assert rule_of(engine, "why is the sky blue")[0] == "fallback_world_answer"

    def test_two_questions_in_one_message(self, engine):
        reply = rule_of(engine, "whats your name and how old are you")[1]
        assert "Buddy" in reply and "old" in reply

    @pytest.mark.parametrize("message,facts,name,expected", [
        ("what's my name", {}, "Lily", "Your name is Lily! I remember."),
        ("what's my name", {}, None, "Hmm, I don't know it yet! What's your name?"),
        ("what is my favorite color", {"favorite_color": "purple"}, "Lily", "Your favorite color is purple! I remember."),
        ("do you remember my dog", {"dog_max": "Max"}, "Lily", "Of course! Your dog Max! How is Max doing?"),
        ("do you remember my cat", {"dog_max": "Max"}, "Lily", "Hmm, I don't think you've told me about your cat yet. Tell me!"),
        ("do you remember me", {}, "Lily", "Of course I remember you, Lily!"),
    ])
    def test_recalls_what_the_child_said(self, engine, message, facts, name, expected):
        reply = engine.generate_response(message, make_personality(), {"known_facts": facts}, user_name=name)
        assert reply == expected

    def test_whats_my_name_is_not_a_name(self, engine):
        assert ("basic", "name", "What") not in engine.extract_memories("what's my name")

    def test_mine_is_not_a_thing(self, engine):
        rule_of(engine, "my favorite food is sushi")
        assert "mine" not in engine.resolve_references("my mom doesnt like it", 1)

    def test_plural_thing_takes_are(self, engine):
        engine.record_bot_reply(1, "I love telling jokes and learning fun facts! What do you like to do?")
        assert engine.resolve_references("thats cool", 1) == "The fun facts are cool"

    def test_fair_is_not_a_reference(self, engine):
        rule_of(engine, "my sister always takes my stuff")
        assert engine.resolve_references("it's not fair", 1) == "it's not fair"

    def test_exclamation_in_bot_reply_is_not_a_thing(self, engine):
        rule_of(engine, "I built a castle yesterday")
        engine.record_bot_reply(1, "Awesome! You built a castle yesterday? That's awesome!")
        assert engine.resolve_references("it has a moat", 1) == "The castle has a moat"

    def test_added_joke_is_not_the_latest_thing(self, engine):
        engine.references.record_bot_reply(1, "Mine is Minecraft.", told="joke", mentions=["Minecraft"],
                                           told_was_added=True)
        assert engine.resolve_references("why do you like it", 1) == "why do you like Minecraft"

    def test_missing_name_is_left_out(self, engine):
        reply = engine.generate_response("bye", make_personality(), user_name=None)
        assert "\x00" not in reply and " ," not in reply and " !" not in reply


class TestRoundSix:
    def test_contraction_is_joined(self, engine):
        assert "you 're" not in rule_of(engine, "I'm good at math")[1]

    def test_pillow_fight_is_not_sad(self, engine):
        assert rule_of(engine, "we had a pillow fight")[0] != "fallback_reflection_sad"

    def test_laughing_so_hard_is_not_sad(self, engine):
        assert rule_of(engine, "we were laughing so hard")[0] != "fallback_reflection_sad"

    @pytest.mark.parametrize("message", ["kids chased me", "mom told us to stop"])
    def test_bare_people_subjects_are_reflected(self, engine, message):
        assert rule_of(engine, message)[0].startswith("fallback_reflection")

    def test_kids_are_not_it(self, engine):
        rule_of(engine, "kids chased me")
        assert not engine.resolve_references("it was fun", 1).lower().startswith("kids was")

    def test_they_after_kids_at_school(self, engine):
        rule_of(engine, "kids at school take my stuff and push me")
        assert engine.resolve_references("they do it every day", 1) == "Kids at school do it every day"


class TestNormalization:
    @pytest.mark.parametrize("text,expected", [
        ("shes nice", "she's nice"),
        ("idk", "I don't know"),
        ("nm u", "not much you"),
        ("its so boring", "it's so boring"),
        ("its wings", "its wings"),
        ("ok ill try that", "ok I'll try that"),
        ("fine ill eat broccoli", "fine I'll eat broccoli"),
        ("a snowman named frosty", "a snowman named Frosty"),
        ("their names are luna and milo", "their names are Luna and Milo"),
        ("he lives in florida", "he lives in Florida"),
        ("its math", "it's math"),
        ("named after my grandpa", "named after my grandpa"),
        ("I feel ill", "I feel ill"),
        ("ur weird", "you're weird"),
        ("ur dog", "your dog"),
        ("my teacher mr kim", "my teacher Mr Kim"),
        ("gtg bye", "got to go bye"),
        ("jk", "just kidding"),
        ("hii", "hi"),
        ("heyyy", "hey"),
        ("I GOT A PUPPY TODAY", "I got a puppy today"),
        ("my cat is fluffy 😻", "my cat is fluffy"),
        ("i lik minecraft alot", "I like minecraft a lot"),
        ("its rlly big", "it's really big"),
        ("whats your name and how old are you", "what's your name? how old are you"),
        ("I went home and what a day", "I went home and what a day"),
        ("I love NASA", "I love NASA"),
        ("my moms room", "my mom's room"),
        ("my moms are nice", "my moms are nice"),
    ])
    def test_normalize(self, text, expected):
        assert UtteranceParser.normalize(text) == expected


class TestSafetyAndEmojis:
    def test_sibling_taking_stuff_is_not_bullying(self):
        result = safety_filter.check_message("she always takes my stuff",
                                             resolved_message="My little sister Ava always takes my stuff")
        assert "bullying" not in result["flags"]

    def test_taking_stuff_without_family_is_still_bullying(self):
        assert "bullying" in safety_filter.check_message("He takes my stuff")["flags"]

    def test_what_if_worry_is_not_bullying(self):
        assert "bullying" not in safety_filter.check_message("what if nobody likes me")["flags"]
        assert "bullying" in safety_filter.check_message("nobody likes me")["flags"]

    def test_where_do_you_live_is_allowed(self):
        assert safety_filter.check_message("where do you live")["safe"]

    @pytest.mark.parametrize("text,negative", [
        ("my grandpa is in the hospital", True),
        ("I wasn't scared", False),
        ("I'm not sad", False),
        ("we buried him", True),
        ("we had a pillow fight", False),
        ("Wow, you lost a tooth?", False),
        ("we were laughing so hard", False),
        ("today was the worst day", True),
        ("she came home from the hospital", False),
    ])
    def test_is_negative(self, text, negative):
        assert emoji_quirk_service.is_negative(text) is negative


# ----------------------------------------------------------------------
# Through the API
# ----------------------------------------------------------------------

_user_ids = itertools.count(9100)


@pytest.fixture(scope="module")
def api():
    logging.disable(logging.CRITICAL)
    with patch("utils.config.settings.USE_LLM", False), TestClient(app) as client:
        yield client
    logging.disable(logging.NOTSET)


def start(api):
    user_id = next(_user_ids)
    response = api.post(f"/api/conversation/start?user_id={user_id}").json()
    return user_id, response["conversation_id"], response["greeting"]


def send(api, user_id, conversation_id, text):
    response = api.post("/api/message",
                        json={"content": text, "conversation_id": conversation_id, "user_id": user_id})
    assert response.status_code == 200
    return response.json()["content"]


def memories(api, user_id):
    response = api.get(f"/api/profile/memories?user_id={user_id}").json()["memories"]
    return {(m["category"], m["key"]): m["value"] for m in response}


class TestConversation:
    def test_hi_after_the_name_question_asks_again(self, api):
        user_id, conversation_id, greeting = start(api)
        assert greeting.endswith("What's your name?")
        reply = send(api, user_id, conversation_id, "hi")
        assert "What's your name?" in reply
        assert "User" not in reply

    @pytest.mark.parametrize("answer", ["im Lily", "lily", "Hi I'm Lily"])
    def test_name_answer_is_remembered(self, api, answer):
        user_id, conversation_id, _ = start(api)
        reply = send(api, user_id, conversation_id, answer)
        assert "Lily" in reply
        assert memories(api, user_id)[("basic", "name")] == "Lily"

    @pytest.mark.parametrize("greeting", ["hii", "HEYYY"])
    def test_stretched_greeting_is_not_a_name(self, api, greeting):
        user_id, conversation_id, _ = start(api)
        send(api, user_id, conversation_id, greeting)
        assert ("basic", "name") not in memories(api, user_id)

    def test_capital_name(self, api):
        user_id, conversation_id, _ = start(api)
        send(api, user_id, conversation_id, "IM SAM")
        assert memories(api, user_id)[("basic", "name")] == "Sam"

    def test_remembers_across_conversations(self, api):
        user_id, conversation_id, _ = start(api)
        for message in ("im lily", "I have a dog named Max", "my favorite color is purple"):
            send(api, user_id, conversation_id, message)
        conversation_id = api.post(f"/api/conversation/start?user_id={user_id}").json()["conversation_id"]
        assert "Lily" in send(api, user_id, conversation_id, "whats my name")
        assert "purple" in send(api, user_id, conversation_id, "what is my favorite color")
        assert "Max" in send(api, user_id, conversation_id, "do you remember my dog")

    def test_feeling_is_not_a_name(self, api):
        user_id, conversation_id, _ = start(api)
        send(api, user_id, conversation_id, "im sad")
        assert ("basic", "name") not in memories(api, user_id)

    def test_answer_to_another_question_is_not_a_name(self, api):
        user_id, conversation_id, _ = start(api)
        send(api, user_id, conversation_id, "do you like pizza or tacos")
        send(api, user_id, conversation_id, "tacos")
        assert ("basic", "name") not in memories(api, user_id)

    def test_sibling_taking_stuff_gets_a_normal_reply(self, api):
        user_id, conversation_id, _ = start(api)
        send(api, user_id, conversation_id, "I have a little sister named Ava")
        reply = send(api, user_id, conversation_id, "she always takes my stuff")
        assert "Bullying" not in reply

    def test_no_jokes_after_sad_news(self, api):
        user_id, conversation_id, _ = start(api)
        with patch("services.conversation_manager.ConversationManager._choose_joke", return_value="pun"):
            for message in ("my grandpa is in the hospital", "we visited him on sunday", "he gave me a hug"):
                reply = send(api, user_id, conversation_id, message)
                assert "joke" not in reply.lower() and "fun one" not in reply.lower()

    def test_hoping_someone_gets_better_stays_gentle(self, api):
        user_id, conversation_id, _ = start(api)
        with patch("services.conversation_manager.ConversationManager._choose_joke", return_value="pun"):
            for message in ("my friend is sick", "I made him a card", "I hope he gets better"):
                reply = send(api, user_id, conversation_id, message)
                assert "joke" not in reply.lower() and "fun one" not in reply.lower()

    def test_generic_advice_when_no_template_matches(self, api):
        user_id, conversation_id, _ = start(api)
        reply = send(api, user_id, conversation_id, "what do you think I should do?")
        assert "trust" in reply  # both generic advice replies mention someone you trust

    def test_check_in_greeting_after_sad_news(self, api):
        user_id, conversation_id, _ = start(api)
        for message in ("im noah", "my grandma is in the hospital"):
            send(api, user_id, conversation_id, message)
        greeting = api.post(f"/api/conversation/start?user_id={user_id}").json()["greeting"]
        assert "I've been thinking about you" in greeting

    def test_no_check_in_greeting_after_happy_talk(self, api):
        user_id, conversation_id, _ = start(api)
        for message in ("im noah", "I have a spelling test tomorrow"):
            send(api, user_id, conversation_id, message)
        greeting = api.post(f"/api/conversation/start?user_id={user_id}").json()["greeting"]
        assert "thinking about you" not in greeting

    def test_remember_thing_from_recent_messages(self, api):
        user_id, conversation_id, _ = start(api)
        send(api, user_id, conversation_id, "I have a spelling test tomorrow")
        reply = send(api, user_id, conversation_id, "remember my spelling test")
        assert "your spelling test" in reply and "your your" not in reply

    @pytest.mark.parametrize("problem,question,word", [
        ("my brother keeps taking my toys", "how do i get him to stop", "mom or dad"),
        ("my friend told everyone my secret", "what should i do", "friend"),
        ("I have a speech at school tomorrow", "any tips", "practic"),
    ])
    def test_advice_follows_the_topic(self, api, problem, question, word):
        user_id, conversation_id, _ = start(api)
        send(api, user_id, conversation_id, problem)
        assert word in send(api, user_id, conversation_id, question)

    def test_gentle_reply_about_a_new_pet_after_one_died(self, api):
        user_id, conversation_id, _ = start(api)
        for message in ("my hamster died yesterday", "his name was peanut"):
            send(api, user_id, conversation_id, message)
        reply = send(api, user_id, conversation_id, "my mom said we can get a new one")
        assert "not ready" in reply and "Yay" not in reply

    def test_known_pet_name_is_capitalized_next_conversation(self, api):
        user_id, conversation_id, _ = start(api)
        send(api, user_id, conversation_id, "I have a dog named max")
        conversation_id = api.post(f"/api/conversation/start?user_id={user_id}").json()["conversation_id"]
        reply = send(api, user_id, conversation_id, "max learned a new trick")
        assert "Max learned" in reply

    def test_name_correction(self, api):
        user_id, conversation_id, _ = start(api)
        send(api, user_id, conversation_id, "im potato")
        send(api, user_id, conversation_id, "lol jk im finn")
        assert memories(api, user_id)[("basic", "name")] == "Finn"
        assert "Finn" in send(api, user_id, conversation_id, "bye")

    def test_no_joke_after_news_about_a_person(self, api):
        user_id, conversation_id, _ = start(api)
        with patch("services.conversation_manager.ConversationManager._choose_joke", return_value="pun"), \
                patch("services.conversation_manager.ConversationManager._invites_answer", return_value=False), \
                patch("services.conversation_manager.pun_quirk_service.add_pun", side_effect=lambda r, **k: r + " PUN"):
            assert "PUN" not in send(api, user_id, conversation_id, "my teacher is mrs brown")
            assert "PUN" in send(api, user_id, conversation_id, "pizza is yummy")

    def test_gentle_dont_know_after_sad_news(self, api):
        user_id, conversation_id, _ = start(api)
        send(api, user_id, conversation_id, "my parents are getting divorced")
        reply = send(api, user_id, conversation_id, "i dont know")
        assert "a lot to think about" in reply
