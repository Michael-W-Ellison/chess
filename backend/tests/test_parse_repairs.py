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


class TestRoundThree:
    @pytest.fixture
    def engine(self):
        import random
        from services.response_engine import ResponseEngine
        return ResponseEngine(rng=random.Random(0))

    @pytest.mark.parametrize("text,rule,reply", [
        ("im ted", "im_name", "Nice to meet you, Ted! I'm Buddy."),
        ("im Sofia", "im_name", "Nice to meet you, Sofia! I'm Buddy."),
        ("my dog is bigger then your dog", "compare_bot_thing",
         "I don't have a dog, since I'm a computer program, but your dog sounds really big!"),
        ("tomorrow is saturday", "day_is", "Ooh, Saturday! Do you have anything fun planned?"),
        ("today is Halloween", "day_is", "Ooh, Halloween! Do you have anything fun planned?"),
        ("my tummy feels funny", "body_feels",
         "Oh no, your tummy feels funny? I'm sorry. Make sure you tell a grown-up so they can help!"),
        ("santa is coming", "fallback_reflection_present_other", "Oh, Santa is coming? Tell me more!"),
        ("santa came last night", "fallback_reflection", "So Santa came last night? What happened next?"),
        ("maya is my friend", "person_relation", "Tell me more about Maya!"),
        ("i got a lego set", "got_gift", "Yay, a LEGO set! Do you like it?"),
        ("i want a Puppy", "want_thing", "Ooh, a Puppy would be so fun! Why do you want one?"),
    ])
    def test_reply(self, engine, text, rule, reply):
        from tests.test_dialogue_fixes import rule_of
        assert rule_of(engine, text) == (rule, reply)

    @pytest.mark.parametrize("text", ["i'm hungry", "im starving"])
    def test_hungry(self, engine, text):
        from tests.test_dialogue_fixes import rule_of
        assert rule_of(engine, text)[0] == "hungry"

    def test_whiskers_is_a_name(self, engine):
        from tests.test_dialogue_fixes import rule_of
        assert "your cat Whiskers was sleeping" in rule_of(engine, "my cat whiskers was sleeping")[1]

    def test_goodnight_still_works(self, engine):
        from tests.test_dialogue_fixes import rule_of
        assert rule_of(engine, "goodnight")[0] == "goodnight"
        assert rule_of(engine, "night night")[0] == "goodnight"


@pytest.mark.parametrize("text,normalized", [
    ("i planted a seed", "I planted a seed"),
    ("y is the sky blue", "why is the sky blue"),
    ("i'm a dinosaur rawr", "I'm a dinosaur! rawr"),
    ("what does gravity mean", "what is gravity"),
    ("what does that mean", "what does that mean"),
    ("i watched frozen", "I watched Frozen"),
    ("i like frozen yogurt", "I like frozen yogurt"),
    ("we saw cars today", "we saw cars today"),
])
def test_round_four_text(text, normalized):
    assert parser.parse(text).text == normalized


def test_pronoun_after_giving_verb_is_the_receiver():
    doc = parser.parse("i made you a card")
    assert token(doc, "you").dep_ == "dative" and token(doc, "card").dep_ == "dobj"


def test_second_subject_after_be_is_its_complement():
    assert token(parser.parse("tag you're it"), "it").dep_ == "attr"


def test_two_word_person_name():
    doc = parser.parse("do you like taylor swift")
    assert token(doc, "swift").pos_ == "PROPN"


class TestRoundFour:
    @pytest.fixture
    def engine(self):
        import random
        from services.response_engine import ResponseEngine
        return ResponseEngine(rng=random.Random(0))

    @pytest.mark.parametrize("text,rule", [
        ("tag you're it", "tag_youre_it"),
        ("pretend you're a cat", "pretend_bot_is"),
        ("look what i made", "show_bot"),
        ("i want to show you something", "show_bot"),
        ("i have a question", "have_question"),
        ("can i tell you something", "tell_bot_something"),
        ("do you know what", "you_know_what"),
        ("what does that mean", "what_does_that_mean"),
        ("can we play later", "play_later"),
        ("i got a red card", "penalty_card"),
        ("i got a birthday card", "got_gift"),
        ("my bike got stolen", "stolen"),
        ("someone took my lunch", "stolen"),
        ("i can't find my dog", "cant_find"),
        ("it's freezing", "weather_temperature"),
        ("it's so hot today", "weather_temperature"),
        ("what does gravity mean", "fallback_world_answer"),
    ])
    def test_rule(self, engine, text, rule):
        from tests.test_dialogue_fixes import rule_of
        assert rule_of(engine, text)[0] == rule

    @pytest.mark.parametrize("text,words", [
        ("i made you a card", "you made me a card"),
        ("i was scared because it was dark", "because it was dark"),
        ("do you like taylor swift", "Taylor Swift"),
        ("i cried when my fish died", "sorry your fish died"),
        ("i like frozen yogurt", "frozen yogurt"),
    ])
    def test_wording(self, engine, text, words):
        from tests.test_dialogue_fixes import rule_of
        assert words in rule_of(engine, text)[1]


@pytest.mark.parametrize("text,normalized", [
    ("i like the book wings of fire", "I like the book Wings of Fire"),
    ("we sang the song baby shark", "we sang the song Baby Shark"),
    ("the movie scared me", "the movie scared me"),
    ("i read the book yesterday", "I read the book yesterday"),
    ("i read a book about sharks", "I read a book about sharks"),
])
def test_titles_after_kind_words(text, normalized):
    assert parser.parse(text).text == normalized


class TestRoundFive:
    @pytest.fixture
    def engine(self):
        import random
        from services.response_engine import ResponseEngine
        return ResponseEngine(rng=random.Random(0))

    @pytest.mark.parametrize("text,rule,reply", [
        ("my favorite animal is a dolphin", "favorite_is", "A dolphin? Mine too! Great minds think alike."),
        ("i'm a dinosaur rawr", "pretend_i_am", "Whoa, a dinosaur! I'd better watch out! What does a dinosaur like to do?"),
        ("i drew a picture of you", "made_for_bot",
         "Aw, you made that for me? That's so sweet! Can you tell me what it looks like?"),
        ("i'm learning to read", "learning_skill",
         "Ooh, you're learning to read? That's a great thing to work on! How's it going so far?"),
    ])
    def test_reply(self, engine, text, rule, reply):
        from tests.test_dialogue_fixes import rule_of
        assert rule_of(engine, text) == (rule, reply)

    def test_not_pretend(self, engine):
        from tests.test_dialogue_fixes import rule_of
        assert rule_of(engine, "i am a kid")[0] != "pretend_i_am"

    def test_other_favorite_still_named(self, engine):
        from tests.test_dialogue_fixes import rule_of
        assert "Mine is dolphins" in rule_of(engine, "my favorite animal is a cat")[1]


@pytest.mark.parametrize("text,normalized", [
    ("my mom n dad took me to the park", "my mom and dad took me to the park"),
    ("i went w/ my grandma", "I went with my grandma"),
    ("i ate b4 school", "I ate before school"),
    ("2day was fun", "today was fun"),
    ("see u l8r", "see you later"),
    ("i'm going 2 the store", "I'm going to the store"),
    ("i have 2 dogs", "I have 2 dogs"),
    ("i have lotsa homework", "I have lots of homework"),
    ("i went home.it was fun", "I went home. it was fun"),
    ("you like pizza right", "do you like pizza?"),
    ("dogs are cute aren't they", "dogs are cute"),
    ("that's right", "that's right"),
    ("turn right", "turn right"),
    ("i did it right", "I did it right"),
    ("the name is not right", "the name is not right"),
    ("i dare you to say something funny", "say something funny"),
])
def test_shorthand(text, normalized):
    assert UtteranceParser.normalize(text) == normalized


class TestRoundSix:
    @pytest.fixture
    def engine(self):
        import random
        from services.response_engine import ResponseEngine
        return ResponseEngine(rng=random.Random(0))

    @pytest.mark.parametrize("text,rule", [
        ("i'm not good at anything", "not_good_at_anything"),
        ("i can't do anything right", "not_good_at_anything"),
        ("i'm not good at math", "not_good_at"),
        ("i'm really good at drawing", "good_at"),
        ("i'm better than my brother at math", "better_than"),
        ("my friend is better than me at reading", "better_than"),
        ("i threw up at school", "sick"),
        ("last week i got sick", "sick"),
        ("my nose is runny", "body_feels"),
        ("i got 3rd place", "achievement"),
        ("I got an A on my spelling test", "achievement"),
        ("i got braces", "got_medical"),
        ("my brother always gets his way", "gets_their_way"),
        ("i have nobody to play with", "left_out"),
        ("no one wanted to sit with me", "left_out"),
        ("i bet you can't guess", "bet_cant_guess"),
        ("tell me something cool", "request_something"),
        ("are dragons real", "fallback_world_answer"),
        ("when is christmas", "fallback_world_answer"),
        ("what time is it", "fallback_world_answer"),
    ])
    def test_rule(self, engine, text, rule):
        from tests.test_dialogue_fixes import rule_of
        assert rule_of(engine, text)[0] == rule

    @pytest.mark.parametrize("text", ["i got ice cream", "we got ice cream and then we went home"])
    def test_getting_food_is_not_an_achievement(self, engine, text):
        from tests.test_dialogue_fixes import rule_of
        assert rule_of(engine, text)[0] != "achievement"


def test_object_of_like_with_question_mark():
    assert token(parser.parse("do you like pizza?"), "pizza").dep_ == "dobj"


class TestRoundSixReplies:
    @pytest.fixture
    def engine(self):
        import random
        from services.response_engine import ResponseEngine
        return ResponseEngine(rng=random.Random(0))

    @pytest.mark.parametrize("text,rule", [
        ("do you like pizza?", "bot_like_food"),
        ("you like pizza right", "bot_like_food"),
        ("dogs are cute aren't they", "pet_cute"),
        ("i got a victory royale", "achievement"),
    ])
    def test_rule(self, engine, text, rule):
        from tests.test_dialogue_fixes import rule_of
        assert rule_of(engine, text)[0] == rule

    def test_superlative_with_a_place_is_not_the_world_answer(self, engine):
        from tests.test_dialogue_fixes import rule_of
        assert "Everest" not in rule_of(engine, "what is the tallest mountain in peru?")[1]
        assert "Everest" in rule_of(engine, "what is the tallest mountain in the world")[1]

    def test_body_reply_uses_the_childs_verb(self, engine):
        from tests.test_dialogue_fixes import rule_of
        assert "your nose is runny?" in rule_of(engine, "my nose is runny")[1]
