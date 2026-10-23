"""
Parse repairs in services/utterance_parser.py for child phrasings the spaCy model misreads.
Skipped when spaCy or its English model is not installed.
"""

import pytest

from services.utterance_parser import UtteranceParser

parser = UtteranceParser()

pytestmark = pytest.mark.skipif(not parser.is_available(), reason="spaCy model en_core_web_sm not installed")


def token(doc, word):
    return next(t for t in doc if t.lower_ == word)


@pytest.mark.parametrize("text,word", [
    ("my dog snores", "snores"),
    ("the baby cries", "cries"),
    ("can fish swim", "swim"),
    ("do dogs dance", "dance"),
    ("i love to camp", "camp"),
    ("i have to camp today", "camp"),
    ("lets paint", "paint"),
    ("lets race", "race"),
])
def test_verb_is_tagged_verb(text, word):
    assert token(parser.parse(text), word).pos_ == "VERB"


def test_like_before_gerund_is_the_main_verb():
    doc = parser.parse("i like jumping")
    like, jumping = token(doc, "like"), token(doc, "jumping")
    assert like.dep_ == "ROOT" and like.pos_ == "VERB"
    assert jumping.dep_ == "xcomp" and jumping.head.i == like.i


@pytest.mark.parametrize("text,name", [
    ("maya and i went to the park", "maya"),
    ("me and lily played tag", "lily"),
])
def test_name_and_i_is_a_shared_subject(text, name):
    doc = parser.parse(text)
    subject, me = token(doc, name), token(doc, "i")
    assert subject.dep_ == "nsubj" and subject.head.pos_ == "VERB"
    assert me.dep_ == "conj" and me.head.i == subject.i


def test_me_and_is_rewritten():
    assert parser.parse("me and my friend built a fort").text.lower().startswith("my friend and i")


@pytest.mark.parametrize("text,word", [("then and i went home", "then"), ("today and tomorrow i have school", "today")])
def test_time_words_are_not_made_subjects(text, word):
    assert token(parser.parse(text), word).dep_ != "nsubj"


def test_me_and_possessive_is_left_alone():
    assert parser.parse("me and my mom's dog ran").text.lower().startswith("me and my mom's")


def test_activity_after_go_is_a_verb():
    swimming = token(parser.parse("let's go swimming"), "swimming")
    assert swimming.dep_ == "xcomp" and swimming.head.lower_ == "go"


class TestLetsSuggestions:
    @pytest.fixture
    def engine(self):
        import random
        from services.response_engine import ResponseEngine
        return ResponseEngine(rng=random.Random(0))

    @pytest.mark.parametrize("text,activity", [
        ("lets paint", "paint"),
        ("lets play tag", "play tag"),
        ("let's go swimming", "go swimming"),
        ("lets go to the park tomorrow", "go to the park"),
    ])
    def test_lets_activity(self, engine, text, activity):
        from tests.test_dialogue_fixes import rule_of
        rule, reply = rule_of(engine, text)
        assert rule == "lets_activity" and reply.startswith(f"I wish I could {activity} with you!")

    @pytest.mark.parametrize("text,topic", [
        ("let's talk about dogs", "dogs"),
        ("can we talk about dogs", "dogs"),
        ("i want to talk about my dog", "your dog"),
    ])
    def test_talk_about(self, engine, text, topic):
        from tests.test_dialogue_fixes import rule_of
        assert rule_of(engine, text) == ("talk_about", f"Sure, let's talk about {topic}! What do you want to tell me?")

    @pytest.mark.parametrize("text", ["let me think", "let him go", "we talked about dogs at school"])
    def test_not_a_suggestion(self, engine, text):
        from tests.test_dialogue_fixes import rule_of
        assert rule_of(engine, text)[0] not in ("lets_activity", "talk_about")

    def test_lets_be_friends(self, engine):
        from tests.test_dialogue_fixes import rule_of
        assert rule_of(engine, "lets be friends")[0] == "lets_be_friends"


@pytest.mark.parametrize("text,word", [("does your dog bark", "bark"), ("grandpa snores really loud", "snores")])
def test_more_verbs_tagged_verb(text, word):
    verb = token(parser.parse(text), word)
    assert verb.pos_ == "VERB" and verb.dep_ == "ROOT"


def test_acomp_after_be_is_an_adjective():
    assert token(parser.parse("theyre so mean"), "mean").pos_ == "ADJ"


@pytest.mark.parametrize("text,name", [("my friend ava came over", "ava"), ("my dog coco ran away", "coco")])
def test_name_after_relation_is_a_name(text, name):
    assert token(parser.parse(text), name).pos_ == "PROPN"


def test_compound_noun_after_pet_is_not_a_name():
    assert token(parser.parse("my dog food spilled"), "food").pos_ == "NOUN"


@pytest.mark.parametrize("text,normalized", [
    ("i goed to the store", "I went to the store"),
    ("we runned so fast", "we ran so fast"),
    ("youre funny", "you're funny"),
    ("that was sooooo fun", "that was so fun"),
    ("it was cooool", "it was cool"),
    ("yesss", "yes"),
    ("my dog is bigger then your dog", "my dog is bigger than your dog"),
    ("buddy do you like pizza", "do you like pizza"),
    ("i love you buddy", "I love you"),
    ("my dog buddy is cute", "my dog buddy is cute"),
    ("we went to the zoo we saw a lion", "we went to the zoo. we saw a lion"),
    ("i saw a dog it was big", "I saw a dog. it was big"),
    ("i have a dog he is cute", "I have a dog. he is cute"),
])
def test_text_fixes(text, normalized):
    assert parser.parse(text).text == normalized


@pytest.mark.parametrize("text", [
    "the cake i made was good", "i think we should go", "i told my mom it was an accident",
    "the toy you gave me broke", "i am scared it will hurt", "im glad you came", "we ate dinner then we played",
])
def test_one_clause_is_not_split(text):
    assert len(list(parser.parse(text).sents)) == 1


class TestReplies:
    @pytest.fixture
    def engine(self):
        import random
        from services.response_engine import ResponseEngine
        return ResponseEngine(rng=random.Random(0))

    @pytest.mark.parametrize("text,rule", [
        ("recess is my favorite", "favorite_self"),
        ("i love you buddy", "love_bot"),
        ("i like you", "love_bot"),
        ("i dont like you", "hate_you"),
        ("i hate you", "hate_you"),
        ("do you love me", "love_bot_question"),
        ("lets not be friends", "lets_not_be_friends"),
    ])
    def test_rule(self, engine, text, rule):
        from tests.test_dialogue_fixes import rule_of
        assert rule_of(engine, text)[0] == rule

    @pytest.mark.parametrize("text,reply", [
        ("my mom wants to talk about my grades", "Your mom wants to talk about your grades? How do you feel about that?"),
        ("my sister wants a puppy", "Your sister wants a puppy? How do you feel about that?"),
    ])
    def test_someone_elses_wish(self, engine, text, reply):
        from tests.test_dialogue_fixes import rule_of
        assert rule_of(engine, text)[1] == reply

    @pytest.mark.parametrize("text,words", [
        ("me and lily played tag", "you and Lily played tag"),
        ("i played with sam today", "with Sam"),
        ("my friend ava came over", "your friend Ava came over"),
    ])
    def test_lowercase_names_capitalized(self, engine, text, words):
        from tests.test_dialogue_fixes import rule_of
        assert words in rule_of(engine, text)[1]

    def test_dog_food_is_not_a_pet(self, engine):
        from tests.test_dialogue_fixes import rule_of
        assert "Pets" not in rule_of(engine, "my dog food spilled")[1]

    def test_working_at_a_hospital_is_not_sad(self, engine):
        from tests.test_dialogue_fixes import rule_of
        assert rule_of(engine, "mommy works at a hospital")[0] != "fallback_reflection_sad"
        assert rule_of(engine, "my grandma is in the hospital")[0] == "fallback_reflection_sad"


@pytest.mark.parametrize("text,normalized", [
    ("your so funny", "you're so funny"),
    ("your the best", "you're the best"),
    ("your funny face", "your funny face"),
    ("i have to much homework", "I have too much homework"),
    ("its to hot outside", "it's too hot outside"),
    ("i went to big bear", "I went to big bear"),
    ("i could of won", "I could have won"),
    ("that is so wierd", "that is so weird"),
    ("there dog is so cute", "their dog is so cute"),
    ("i like there house", "I like their house"),
    ("there going to the park", "they're going to the park"),
    ("i went there today", "I went there today"),
    ("there is a dog", "there is a dog"),
])
def test_homophones_and_spellings(text, normalized):
    assert parser.parse(text).text == normalized


@pytest.mark.parametrize("text,subject", [("a spider bit me", "spider"), ("a mosquito bit me", "mosquito"),
                                          ("a bee stung me", "bee")])
def test_creature_did_it(text, subject):
    doc = parser.parse(text)
    noun = token(doc, subject)
    assert noun.dep_ == "nsubj" and noun.pos_ == "NOUN" and noun.head.pos_ == "VERB"
    assert token(doc, "me").dep_ == "dobj"


class TestMoreReplies:
    @pytest.fixture
    def engine(self):
        import random
        from services.response_engine import ResponseEngine
        return ResponseEngine(rng=random.Random(0))

    @pytest.mark.parametrize("text,reply", [
        ("a bee chased me", "So a bee chased you? What happened next?"),
        ("the power went out", "So the power went out? What happened next?"),
    ])
    def test_reflection(self, engine, text, reply):
        from tests.test_dialogue_fixes import rule_of
        assert rule_of(engine, text)[1] == reply

    @pytest.mark.parametrize("text,rule", [
        ("i got stung by a bee", "fallback_appraisal_harm_real"),
        ("a spider bit me", "fallback_appraisal_harm_real"),
        ("i have a loose tooth", "loose_tooth"),
        ("your so funny", "bot_compliment"),
    ])
    def test_rule(self, engine, text, rule):
        from tests.test_dialogue_fixes import rule_of
        assert rule_of(engine, text)[0] == rule
