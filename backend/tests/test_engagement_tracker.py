"""
Tests for engagement learning (services/engagement_tracker.py) and its use in replies
and personality drift
"""

import random
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.database import Base
from models.engagement import EngagementStat
from models.personality import BotPersonality
from models.conversation import Conversation
from models.user import User
from services.engagement_tracker import (
    MIN_SAMPLES,
    SIGNAL_MIN_SAMPLES,
    EngagementPolicy,
    EngagementTracker,
    score_engagement,
)
from services.utterance_parser import UtteranceParser

needs_parser = pytest.mark.skipif(
    not UtteranceParser().is_available(), reason="spaCy model en_core_web_sm not installed"
)


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    session.add(User(id=1, name="Sam"))
    session.commit()
    yield session
    session.close()


@pytest.fixture
def tracker():
    return EngagementTracker(rng=random.Random(0))


def policy_with(stats):
    """Policy from {(feature, arm): (mean score, count)}"""
    return EngagementPolicy({key: [mean * count, count] for key, (mean, count) in stats.items()},
                            random.Random(0))


class TestScoring:
    def test_brush_off_scores_low(self):
        for message in ["ok", "idk", "whatever", "k", "meh"]:
            assert score_engagement("What was the best part?", message) <= 0.05

    def test_long_on_topic_answer_scores_high(self):
        score = score_engagement(
            "You went to the zoo? What was the best part?",
            "The giraffes at the zoo were the best because they ate leaves right out of my hand",
        )
        assert score >= 0.8

    def test_yes_to_a_question_scores_more_than_unprompted_yes(self):
        assert score_engagement("Do you like it?", "yes") > score_engagement("That's cool.", "yes")

    def test_staying_on_topic_adds_to_score(self):
        on_topic = score_engagement("Tell me about soccer!", "soccer practice was long")
        off_topic = score_engagement("Tell me about soccer!", "my cat sleeps a lot")
        assert on_topic > off_topic

    def test_asking_back_adds_to_score(self):
        assert score_engagement("I like pizza!", "what toppings do you like?") > \
            score_engagement("I like pizza!", "what toppings do you like")

    def test_scores_are_between_0_and_1(self):
        long_message = " ".join(["because I feel"] * 30) + "?"
        assert 0.0 <= score_engagement("Why?", long_message) <= 1.0
        assert score_engagement("Hi!", "") == 0.0


class TestRecording:
    def test_no_pending_reply_records_nothing(self, tracker, db):
        assert tracker.record_response(1, "hello there", db) is None
        assert db.query(EngagementStat).count() == 0

    def test_score_is_credited_to_each_choice(self, tracker, db):
        tracker.set_pending(1, "Cool! What was the best part?", {"follow_up": "yes", "rule": "evaluation"})
        score = tracker.record_response(1, "the best part was the slide at the water park", db)

        rows = {(r.feature, r.arm): r for r in db.query(EngagementStat).all()}
        assert set(rows) == {("follow_up", "yes"), ("rule", "evaluation")}
        assert rows[("follow_up", "yes")].count == 1
        assert rows[("follow_up", "yes")].score_sum == pytest.approx(score)

    def test_totals_accumulate(self, tracker, db):
        for message in ["ok", "it was really fun and I want to go again"]:
            tracker.set_pending(1, "How was it?", {"follow_up": "yes"})
            tracker.record_response(1, message, db)
        row = db.query(EngagementStat).one()
        assert row.count == 2

    def test_pending_is_used_once(self, tracker, db):
        tracker.set_pending(1, "How was it?", {"follow_up": "yes"})
        tracker.record_response(1, "good", db)
        assert tracker.record_response(1, "good", db) is None

    def test_discarded_reply_is_not_scored(self, tracker, db):
        tracker.set_pending(1, "How was it?", {"follow_up": "yes"})
        tracker.discard_pending(1)
        assert tracker.record_response(1, "good", db) is None

    def test_stats_are_loaded_from_the_database(self, tracker, db):
        db.add(EngagementStat(user_id=1, feature="follow_up", arm="yes", score_sum=4.0, count=8))
        db.commit()
        fresh = EngagementTracker()
        assert fresh.policy(1, db).count("follow_up", "yes") == 8


class TestPolicy:
    def test_needs_minimum_samples_for_every_option(self):
        policy = policy_with({("follow_up", "yes"): (0.8, MIN_SAMPLES), ("follow_up", "no"): (0.2, MIN_SAMPLES - 1)})
        assert not policy.has_data("follow_up", ["yes", "no"])

    def test_choose_prefers_the_more_engaging_option(self):
        policy = policy_with({("follow_up", "yes"): (0.8, 30), ("follow_up", "no"): (0.2, 30)})
        choices = [policy.choose("follow_up", {"yes": 0.5, "no": 0.5}) for _ in range(200)]
        assert choices.count("yes") > 180

    def test_weaker_option_is_still_tried_with_little_data(self):
        policy = policy_with({("follow_up", "yes"): (0.6, MIN_SAMPLES), ("follow_up", "no"): (0.4, MIN_SAMPLES)})
        choices = [policy.choose("follow_up", {"yes": 0.5, "no": 0.5}) for _ in range(200)]
        assert 0 < choices.count("no") < choices.count("yes")


class TestTraitSignals:
    def add(self, db, feature, arm, mean, count):
        db.add(EngagementStat(user_id=1, feature=feature, arm=arm, score_sum=mean * count, count=count))
        db.commit()

    def test_clear_preference_gives_signal(self, tracker, db):
        self.add(db, "follow_up", "yes", 0.7, SIGNAL_MIN_SAMPLES)
        self.add(db, "follow_up", "no", 0.3, SIGNAL_MIN_SAMPLES)
        assert tracker.trait_signals(1, db)["curiosity"][0] == 1

    def test_jokes_combine_puns_and_facts(self, tracker, db):
        self.add(db, "humor", "pun", 0.2, SIGNAL_MIN_SAMPLES // 2)
        self.add(db, "humor", "fact", 0.2, SIGNAL_MIN_SAMPLES // 2)
        self.add(db, "humor", "none", 0.6, SIGNAL_MIN_SAMPLES)
        assert tracker.trait_signals(1, db)["humor"][0] == -1

    def test_small_difference_gives_no_signal(self, tracker, db):
        self.add(db, "follow_up", "yes", 0.52, SIGNAL_MIN_SAMPLES)
        self.add(db, "follow_up", "no", 0.48, SIGNAL_MIN_SAMPLES)
        assert tracker.trait_signals(1, db) == {}

    def test_too_few_samples_gives_no_signal(self, tracker, db):
        self.add(db, "follow_up", "yes", 0.9, SIGNAL_MIN_SAMPLES - 1)
        self.add(db, "follow_up", "no", 0.1, SIGNAL_MIN_SAMPLES)
        assert tracker.trait_signals(1, db) == {}


class TestPersonalityDrift:
    def make_personality(self, db, curiosity):
        personality = BotPersonality(user_id=1, name="Buddy", humor=0.5, energy=0.5,
                                     curiosity=curiosity, formality=0.3)
        conversation = Conversation(user_id=1, message_count=0)
        db.add_all([personality, conversation])
        db.commit()
        return personality, conversation

    @pytest.mark.parametrize("direction", [1, -1])
    def test_engagement_signal_moves_curiosity(self, db, direction):
        from services.personality_drift_calculator import personality_drift_calculator

        personality, conversation = self.make_personality(db, curiosity=0.5)
        signal = {"curiosity": (direction, "test signal")}
        with patch("services.engagement_tracker.engagement_tracker.trait_signals", return_value=signal):
            personality_drift_calculator.calculate_drift_after_conversation(personality, conversation, db)
        assert (personality.curiosity - 0.5) * direction > 0

    def test_no_drift_past_the_upper_margin(self, db):
        from services.personality_drift_calculator import personality_drift_calculator

        personality, conversation = self.make_personality(db, curiosity=0.95)
        with patch("services.engagement_tracker.engagement_tracker.trait_signals",
                   return_value={"curiosity": (1, "test signal")}):
            personality_drift_calculator.calculate_drift_after_conversation(personality, conversation, db)
        assert personality.curiosity == pytest.approx(0.95)


@needs_parser
class TestEngineUsesPolicy:
    @pytest.fixture
    def engine(self):
        from services.response_engine import ResponseEngine
        return ResponseEngine(rng=random.Random(0))

    @staticmethod
    def personality(curiosity):
        return SimpleNamespace(id=1, user_id=1, name="Buddy", mood="happy", friendship_level=1,
                               energy=0.7, curiosity=curiosity, formality=0.3, get_interests=lambda: [])

    def follow_up_rate(self, engine, curiosity, policy):
        asked = 0
        for _ in range(60):
            features = {}
            engine.generate_response("I won my soccer game today", self.personality(curiosity),
                                     policy=policy, features=features)
            asked += features.get("follow_up") == "yes"
        return asked / 60

    def test_features_are_recorded(self, engine):
        features = {}
        engine.generate_response("I won my soccer game today", self.personality(1.0), features=features)
        assert features["rule"] == "achievement"
        assert features["follow_up"] == "yes"
        assert "template:achievement" in features

    def test_fallback_features_are_recorded(self, engine):
        features = {}
        engine.generate_response("We went to the zoo", self.personality(0.5), features=features)
        assert features["rule"] == "fallback_reflection"
        assert "template:fallback_reflection" in features

    def test_learning_overrides_curiosity_for_this_child(self, engine):
        dislikes_questions = policy_with({("follow_up", "yes"): (0.1, 30), ("follow_up", "no"): (0.7, 30)})
        assert self.follow_up_rate(engine, curiosity=1.0, policy=None) == 1.0
        assert self.follow_up_rate(engine, curiosity=1.0, policy=dislikes_questions) < 0.2

    def test_without_enough_data_curiosity_decides(self, engine):
        little_data = policy_with({("follow_up", "yes"): (0.1, 2), ("follow_up", "no"): (0.7, 2)})
        assert self.follow_up_rate(engine, curiosity=1.0, policy=little_data) == 1.0

    def test_learned_template_preference(self, engine):
        from services.response_engine import template_id

        templates = engine.kb["fallbacks"]["reflection"]
        favorite = template_id(templates[0])
        stats = {("template:fallback_reflection", template_id(t)): (0.9 if template_id(t) == favorite else 0.1, 30)
                 for t in templates}
        policy = policy_with(stats)
        chosen = []
        for _ in range(30):
            features = {}
            engine.generate_response("We went to the zoo", self.personality(0.0), policy=policy, features=features)
            chosen.append(features["template:fallback_reflection"])
        # Never repeated back to back, and the favorite is used whenever it was not just used
        assert all(a != b for a, b in zip(chosen, chosen[1:]))
        assert chosen.count(favorite) >= 14


def test_parent_engagement_endpoint(client):
    from database.database import init_db

    init_db()  # the client fixture does not run app startup, which creates the tables
    response = client.get("/api/parent/engagement?user_id=1")
    assert response.status_code == 200
    assert response.json()["user_id"] == 1
    assert isinstance(response.json()["stats"], list)
