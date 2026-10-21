"""
Tests for using the stored advice templates in conversations
(advice_template_service.find_relevant_template and the conversation pipeline)
"""


import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.database import Base
from database.seed import seed_advice_templates
from models.personality import BotPersonality
from models.user import User
from services.advice_category_detector import advice_category_detector
from services.advice_template_service import AdviceTemplateService
from services.conversation_manager import ConversationManager


@pytest.fixture
def db():
    """In-memory database with the seeded advice templates and an 11-year-old user"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    seed_advice_templates(session)
    session.add(User(id=1, name="Sam", age=11))
    session.commit()
    yield session
    session.close()


@pytest.fixture
def service():
    return AdviceTemplateService()


class TestFindRelevantTemplate:
    @pytest.mark.parametrize("message,expected", [
        ("How do I stop being nervous before my piano recital?", "Stage fright"),
        ("My parents are fighting a lot. What should I do?", "parents fight"),
        ("My best friend is ignoring me and I don't know what to do", "Friend arguments"),
        ("My sister keeps going into my room, what should I do?", "privacy"),
        ("I'm really stressed about my math test tomorrow, what should I do?", "test"),
    ])
    def test_template_matches_the_message(self, db, service, message, expected):
        template = service.find_relevant_template(db, message, friendship_level=5, age=11)
        assert template is not None
        assert expected.lower() in template.template.lower()

    @pytest.mark.parametrize("message", ["Can you help me with my friend?", "What should I eat for lunch?"])
    def test_no_template_without_a_specific_match(self, db, service, message):
        assert service.find_relevant_template(db, message, friendship_level=5, age=11) is None

    def test_friendship_level_limits_templates(self, db, service):
        message = "How do I stop being nervous before my piano recital?"
        assert service.find_relevant_template(db, message, friendship_level=1, age=11) is None

    def test_age_limits_templates(self, db, service):
        message = "How do I stop being nervous before my piano recital?"
        assert service.find_relevant_template(db, message, friendship_level=5, age=6) is None

    def test_keyword_endings_match(self, db, service):
        assert service._mentions("they keep fighting", "fight")
        assert not service._mentions("a fighter", "fight")

    def test_formatted_advice_uses_the_message(self, db, service):
        advice = service.get_formatted_advice(
            db, category="emotional", friendship_level=5, user_id=1, age=11,
            user_message="How do I stop being nervous before my piano recital?",
        )
        assert "Stage fright" in advice and "Sam" in advice


class TestConversationPipeline:
    def personality(self, db, level):
        personality = BotPersonality(user_id=1, name="Buddy", friendship_level=level, mood="happy",
                                     humor=0.5, energy=0.6, curiosity=0.5, formality=0.3)
        db.add(personality)
        db.commit()
        return personality

    def context(self, message):
        return {"advice_request": advice_category_detector.detect_advice_request(message),
                "detected_mood": "anxious", "recent_messages": [], "relevant_memories": []}

    def test_template_advice_for_a_matching_request(self, db):
        message = "How do I stop being nervous before my piano recital?"
        advice = ConversationManager()._template_advice(message, self.context(message), self.personality(db, 5), db)
        assert "Stage fright" in advice

    def test_no_advice_for_other_messages(self, db):
        message = "I went to the zoo today"
        assert ConversationManager()._template_advice(message, self.context(message), self.personality(db, 5), db) is None

    def test_rule_based_reply_is_the_advice(self):
        features = {}
        reply = ConversationManager()._rule_based_response(
            "How do I stop being nervous?", {"advice": "Take three slow breaths."}, None, True, None, features)
        assert reply == "Take three slow breaths."
        assert features == {"rule": "advice"}

    def test_llm_prompt_includes_the_advice(self, db):
        message = "How do I stop being nervous before my piano recital?"
        context = self.context(message)
        context["advice"] = "Stage fright is normal. Take three slow breaths."
        prompt = ConversationManager()._build_prompt(context, message, self.personality(db, 5))
        assert "ADVICE TO GIVE" in prompt and "Take three slow breaths." in prompt
