"""
Tests for Personality Drift System
Tests drift calculation based on conversation metrics
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.database import Base
from models.user import User
from models.personality import BotPersonality
from models.conversation import Conversation, Message
from models.personality_drift import PersonalityDrift
from services.personality_drift_calculator import (
    PersonalityDriftCalculator,
    personality_drift_calculator,
)


@pytest.fixture
def test_db():
    """Create test database"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture
def test_user(test_db):
    """Create test user"""
    user = User(id=1, name="Test User", age=12, created_at=datetime.now())
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def test_personality(test_db, test_user):
    """Create test personality with default traits"""
    personality = BotPersonality(
        user_id=test_user.id,
        name="TestBot",
        humor=0.5,
        energy=0.5,
        curiosity=0.5,
        formality=0.5,
        friendship_level=3,
        friendship_points=500,
        mood="happy",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    test_db.add(personality)
    test_db.commit()
    test_db.refresh(personality)
    return personality


@pytest.fixture
def test_conversation(test_db, test_user):
    """Create test conversation"""
    conversation = Conversation(
        user_id=test_user.id,
        timestamp=datetime.now(),
        message_count=10,
        duration_seconds=300,
    )
    test_db.add(conversation)
    test_db.commit()
    test_db.refresh(conversation)
    return conversation


class TestPersonalityDriftCalculator:
    """Test personality drift calculator"""

    def test_calculator_initialization(self):
        """Test calculator initializes correctly"""
        calc = PersonalityDriftCalculator()
        assert calc.DRIFT_AMOUNT_SMALL == 0.01
        assert calc.DRIFT_AMOUNT_MEDIUM == 0.03
        assert calc.DRIFT_AMOUNT_LARGE == 0.05
        assert calc.TRAIT_MIN == 0.0
        assert calc.TRAIT_MAX == 1.0

    def test_analyze_conversation_with_laughter(self, test_db, test_conversation):
        """Test conversation analysis detects laughter"""
        calc = PersonalityDriftCalculator()

        # Add messages with laughter
        msg1 = Message(
            conversation_id=test_conversation.id,
            role="user",
            content="haha that's hilarious!",
        )
        msg2 = Message(
            conversation_id=test_conversation.id,
            role="user",
            content="lol you're funny 😂",
        )
        test_db.add_all([msg1, msg2])
        test_db.commit()

        analysis = calc._analyze_conversation(test_conversation, test_db)

        assert analysis["laughter_count"] == 2
        assert analysis["message_count"] == 10

    def test_analyze_conversation_with_feelings(self, test_db, test_conversation):
        """Test conversation analysis detects feelings"""
        calc = PersonalityDriftCalculator()

        # Add messages with feelings
        msg1 = Message(
            conversation_id=test_conversation.id,
            role="user",
            content="I feel really happy today!",
        )
        msg2 = Message(
            conversation_id=test_conversation.id,
            role="user",
            content="I'm feeling a bit worried about the test",
        )
        test_db.add_all([msg1, msg2])
        test_db.commit()

        analysis = calc._analyze_conversation(test_conversation, test_db)

        assert analysis["feelings_count"] == 2

    def test_analyze_conversation_with_questions(self, test_db, test_conversation):
        """Test conversation analysis detects questions"""
        calc = PersonalityDriftCalculator()

        # Add messages with questions
        msg1 = Message(
            conversation_id=test_conversation.id,
            role="user",
            content="What do you think about that?",
        )
        msg2 = Message(
            conversation_id=test_conversation.id,
            role="user",
            content="How does that work?",
        )
        msg3 = Message(
            conversation_id=test_conversation.id,
            role="user",
            content="Can you explain?",
        )
        test_db.add_all([msg1, msg2, msg3])
        test_db.commit()

        analysis = calc._analyze_conversation(test_conversation, test_db)

        assert analysis["questions_count"] == 3

    def test_analyze_conversation_with_casual_language(
        self, test_db, test_conversation
    ):
        """Test conversation analysis detects casual language"""
        calc = PersonalityDriftCalculator()

        # Add messages with casual language
        msg1 = Message(
            conversation_id=test_conversation.id,
            role="user",
            content="yeah that sounds cool btw",
        )
        msg2 = Message(
            conversation_id=test_conversation.id,
            role="user",
            content="nah idk lol",
        )
        test_db.add_all([msg1, msg2])
        test_db.commit()

        analysis = calc._analyze_conversation(test_conversation, test_db)

        assert analysis["casual_language_count"] >= 2

    def test_analyze_conversation_with_deep_topics(self, test_db, test_conversation):
        """Test conversation analysis detects deep topics"""
        calc = PersonalityDriftCalculator()

        # Add messages with deep topics
        msg1 = Message(
            conversation_id=test_conversation.id,
            role="user",
            content="What's the meaning of life?",
        )
        msg2 = Message(
            conversation_id=test_conversation.id,
            role="user",
            content="I'm thinking about my future goals",
        )
        test_db.add_all([msg1, msg2])
        test_db.commit()

        analysis = calc._analyze_conversation(test_conversation, test_db)

        assert analysis["deep_topics_count"] >= 2


class TestHumorDrift:
    """Test humor trait drift calculations"""

    def test_humor_increases_with_laughter(self, test_db, test_personality, test_conversation):
        """Test humor increases when user laughs"""
        calc = PersonalityDriftCalculator()

        # Create conversation with lots of laughter
        for i in range(3):
            msg = Message(
                conversation_id=test_conversation.id,
                role="user",
                content=f"haha that's funny! {i}",
            )
            test_db.add(msg)
        test_db.commit()

        old_humor = test_personality.humor

        # Calculate drift
        drift_events = calc.calculate_drift_after_conversation(
            test_personality, test_conversation, test_db
        )

        # Humor should increase
        assert test_personality.humor > old_humor

        # Should have a humor drift event
        humor_drifts = [d for d in drift_events if d.trait_name == "humor"]
        assert len(humor_drifts) > 0
        assert humor_drifts[0].change_amount > 0

    def test_humor_decreases_with_deep_topics(
        self, test_db, test_personality, test_conversation
    ):
        """Test humor decreases with serious/deep topics"""
        calc = PersonalityDriftCalculator()

        # Create conversation with deep topics
        for i in range(3):
            msg = Message(
                conversation_id=test_conversation.id,
                role="user",
                content=f"I'm worried about my future and life goals {i}",
            )
            test_db.add(msg)
        test_db.commit()

        old_humor = test_personality.humor

        # Calculate drift
        drift_events = calc.calculate_drift_after_conversation(
            test_personality, test_conversation, test_db
        )

        # Humor should decrease or stay same
        humor_drifts = [d for d in drift_events if d.trait_name == "humor"]
        if humor_drifts:
            # If there's a drift, it should be negative
            assert humor_drifts[0].change_amount <= 0


class TestEnergyDrift:
    """Test energy trait drift calculations"""

    def test_energy_increases_with_long_conversation(
        self, test_db, test_personality, test_conversation
    ):
        """Test energy increases with long quality conversations"""
        calc = PersonalityDriftCalculator()

        # Set high message count
        test_conversation.message_count = 25

        # Add many messages
        for i in range(25):
            msg = Message(
                conversation_id=test_conversation.id,
                role="user",
                content=f"This is a substantive message about interesting topics {i}",
            )
            test_db.add(msg)
        test_db.commit()

        old_energy = test_personality.energy

        # Calculate drift
        drift_events = calc.calculate_drift_after_conversation(
            test_personality, test_conversation, test_db
        )

        # Energy should increase
        energy_drifts = [d for d in drift_events if d.trait_name == "energy"]
        assert len(energy_drifts) > 0
        assert energy_drifts[0].change_amount > 0

    def test_energy_decreases_with_short_messages(
        self, test_db, test_personality, test_conversation
    ):
        """Test energy decreases when user sends very short messages"""
        calc = PersonalityDriftCalculator()

        # Add many short messages
        for i in range(10):
            msg = Message(
                conversation_id=test_conversation.id, role="user", content="ok"
            )
            test_db.add(msg)
        test_db.commit()

        old_energy = test_personality.energy

        # Calculate drift
        drift_events = calc.calculate_drift_after_conversation(
            test_personality, test_conversation, test_db
        )

        # Energy should decrease or stay same
        energy_drifts = [d for d in drift_events if d.trait_name == "energy"]
        if energy_drifts:
            assert energy_drifts[0].change_amount <= 0


class TestCuriosityDrift:
    """Test curiosity trait drift calculations"""

    def test_curiosity_increases_with_questions(
        self, test_db, test_personality, test_conversation
    ):
        """Test curiosity increases when user asks questions"""
        calc = PersonalityDriftCalculator()

        # Add messages with questions
        questions = [
            "What do you think?",
            "How does that work?",
            "Can you explain more?",
            "Why is that?",
        ]
        for q in questions:
            msg = Message(
                conversation_id=test_conversation.id, role="user", content=q
            )
            test_db.add(msg)
        test_db.commit()

        old_curiosity = test_personality.curiosity

        # Calculate drift
        drift_events = calc.calculate_drift_after_conversation(
            test_personality, test_conversation, test_db
        )

        # Curiosity should increase
        curiosity_drifts = [d for d in drift_events if d.trait_name == "curiosity"]
        assert len(curiosity_drifts) > 0
        assert curiosity_drifts[0].change_amount > 0

    def test_curiosity_increases_with_feelings_shared(
        self, test_db, test_personality, test_conversation
    ):
        """Test curiosity increases when user shares feelings (trust)"""
        calc = PersonalityDriftCalculator()

        # Add messages sharing feelings
        feelings = [
            "I feel really happy today",
            "I'm feeling a bit worried",
            "I feel excited about this",
        ]
        for feeling in feelings:
            msg = Message(
                conversation_id=test_conversation.id, role="user", content=feeling
            )
            test_db.add(msg)
        test_db.commit()

        old_curiosity = test_personality.curiosity

        # Calculate drift
        drift_events = calc.calculate_drift_after_conversation(
            test_personality, test_conversation, test_db
        )

        # Curiosity should increase
        curiosity_drifts = [d for d in drift_events if d.trait_name == "curiosity"]
        assert len(curiosity_drifts) > 0
        assert curiosity_drifts[0].change_amount > 0


class TestFormalityDrift:
    """Test formality trait drift calculations"""

    def test_formality_decreases_with_casual_language(
        self, test_db, test_personality, test_conversation
    ):
        """Test formality decreases with casual language"""
        calc = PersonalityDriftCalculator()

        # Add messages with casual language
        casual_msgs = [
            "yeah that's cool lol",
            "nah idk btw",
            "yep omg that's awesome",
            "lol yeah totally",
            "nope tbh",
        ]
        for msg_text in casual_msgs:
            msg = Message(
                conversation_id=test_conversation.id, role="user", content=msg_text
            )
            test_db.add(msg)
        test_db.commit()

        old_formality = test_personality.formality

        # Calculate drift
        drift_events = calc.calculate_drift_after_conversation(
            test_personality, test_conversation, test_db
        )

        # Formality should decrease
        formality_drifts = [d for d in drift_events if d.trait_name == "formality"]
        assert len(formality_drifts) > 0
        assert formality_drifts[0].change_amount < 0

    def test_formality_decreases_with_feelings_shared(
        self, test_db, test_personality, test_conversation
    ):
        """Test formality decreases when conversation is personal"""
        calc = PersonalityDriftCalculator()

        # Add messages sharing personal feelings
        for i in range(4):
            msg = Message(
                conversation_id=test_conversation.id,
                role="user",
                content=f"I feel really emotional about this {i}",
            )
            test_db.add(msg)
        test_db.commit()

        old_formality = test_personality.formality

        # Calculate drift
        drift_events = calc.calculate_drift_after_conversation(
            test_personality, test_conversation, test_db
        )

        # Formality should decrease
        formality_drifts = [d for d in drift_events if d.trait_name == "formality"]
        assert len(formality_drifts) > 0
        assert formality_drifts[0].change_amount < 0


class TestDriftBounding:
    """Test drift values stay within bounds"""

    def test_trait_cannot_exceed_max(self, test_db, test_personality, test_conversation):
        """Test traits cannot exceed maximum value"""
        calc = PersonalityDriftCalculator()

        # Set humor very high
        test_personality.humor = 0.98

        # Add lots of laughter to push it over
        for i in range(5):
            msg = Message(
                conversation_id=test_conversation.id,
                role="user",
                content="haha lol that's hilarious 😂",
            )
            test_db.add(msg)
        test_db.commit()

        # Calculate drift
        calc.calculate_drift_after_conversation(
            test_personality, test_conversation, test_db
        )

        # Humor should be capped at 1.0
        assert test_personality.humor <= 1.0

    def test_trait_cannot_go_below_min(
        self, test_db, test_personality, test_conversation
    ):
        """Test traits cannot go below minimum value"""
        calc = PersonalityDriftCalculator()

        # Set formality very low
        test_personality.formality = 0.02

        # Add lots of casual language to push it below 0
        for i in range(10):
            msg = Message(
                conversation_id=test_conversation.id,
                role="user",
                content="yeah lol nah btw omg",
            )
            test_db.add(msg)
        test_db.commit()

        # Calculate drift
        calc.calculate_drift_after_conversation(
            test_personality, test_conversation, test_db
        )

        # Formality should be capped at 0.0
        assert test_personality.formality >= 0.0


class TestManualAdjustment:
    """Test manual trait adjustments"""

    def test_manual_adjustment_works(self, test_db, test_personality):
        """Test manual trait adjustment"""
        calc = PersonalityDriftCalculator()

        old_humor = test_personality.humor

        # Manually adjust humor
        drift_event = calc.manual_trait_adjustment(
            test_personality, "humor", 0.8, test_db
        )

        # Humor should be set to 0.8
        assert test_personality.humor == 0.8
        assert drift_event.trait_name == "humor"
        assert drift_event.trigger_type == "manual"
        assert drift_event.old_value == old_humor
        assert drift_event.new_value == 0.8

    def test_manual_adjustment_validates_trait_name(self, test_db, test_personality):
        """Test manual adjustment validates trait name"""
        calc = PersonalityDriftCalculator()

        with pytest.raises(ValueError, match="Invalid trait name"):
            calc.manual_trait_adjustment(
                test_personality, "invalid_trait", 0.5, test_db
            )

    def test_manual_adjustment_validates_value_range(self, test_db, test_personality):
        """Test manual adjustment validates value range"""
        calc = PersonalityDriftCalculator()

        # Value too high
        with pytest.raises(ValueError, match="must be between"):
            calc.manual_trait_adjustment(test_personality, "humor", 1.5, test_db)

        # Value too low
        with pytest.raises(ValueError, match="must be between"):
            calc.manual_trait_adjustment(test_personality, "humor", -0.5, test_db)


class TestDriftHistory:
    """Test drift history and tracking"""

    def test_get_drift_history(self, test_db, test_user, test_personality, test_conversation):
        """Test getting drift history"""
        calc = PersonalityDriftCalculator()

        # Create some drifts
        for i in range(3):
            msg = Message(
                conversation_id=test_conversation.id,
                role="user",
                content=f"haha funny {i}",
            )
            test_db.add(msg)
        test_db.commit()

        calc.calculate_drift_after_conversation(
            test_personality, test_conversation, test_db
        )

        # Get history
        history = calc.get_drift_history(test_user.id, test_db)

        assert len(history) > 0
        assert all(isinstance(d, PersonalityDrift) for d in history)

    def test_get_drift_history_filtered_by_trait(
        self, test_db, test_user, test_personality, test_conversation
    ):
        """Test getting drift history filtered by trait"""
        calc = PersonalityDriftCalculator()

        # Create drifts
        for i in range(3):
            msg = Message(
                conversation_id=test_conversation.id,
                role="user",
                content="haha lol funny",
            )
            test_db.add(msg)
        test_db.commit()

        calc.calculate_drift_after_conversation(
            test_personality, test_conversation, test_db
        )

        # Get humor history only
        history = calc.get_drift_history(test_user.id, test_db, trait_name="humor")

        assert all(d.trait_name == "humor" for d in history)

    def test_get_drift_summary(self, test_db, test_user, test_personality, test_conversation):
        """Test getting drift summary"""
        calc = PersonalityDriftCalculator()

        # Create some drifts
        for i in range(3):
            msg = Message(
                conversation_id=test_conversation.id,
                role="user",
                content="haha lol 😂",
            )
            test_db.add(msg)
        test_db.commit()

        calc.calculate_drift_after_conversation(
            test_personality, test_conversation, test_db
        )

        # Get summary
        summary = calc.get_drift_summary(test_user.id, test_db)

        assert "total_drifts" in summary
        assert "by_trait" in summary
        assert "by_trigger" in summary
        assert summary["total_drifts"] > 0

    def test_get_trait_timeline(self, test_db, test_user, test_personality, test_conversation):
        """Test getting trait timeline"""
        calc = PersonalityDriftCalculator()

        # Create multiple drifts over time
        for i in range(3):
            msg = Message(
                conversation_id=test_conversation.id,
                role="user",
                content="haha funny",
            )
            test_db.add(msg)
        test_db.commit()

        calc.calculate_drift_after_conversation(
            test_personality, test_conversation, test_db
        )

        # Get timeline
        timeline = calc.get_trait_timeline(test_user.id, "humor", test_db)

        assert isinstance(timeline, list)
        if timeline:
            assert "timestamp" in timeline[0]
            assert "value" in timeline[0]
            assert "change" in timeline[0]
            assert "trigger" in timeline[0]


class TestDriftPersistence:
    """Test drift events are persisted correctly"""

    def test_drift_events_saved_to_database(
        self, test_db, test_personality, test_conversation
    ):
        """Test drift events are saved to database"""
        calc = PersonalityDriftCalculator()

        # Create conversation that will cause drift
        for i in range(3):
            msg = Message(
                conversation_id=test_conversation.id,
                role="user",
                content="lol haha funny",
            )
            test_db.add(msg)
        test_db.commit()

        # Calculate drift
        drift_events = calc.calculate_drift_after_conversation(
            test_personality, test_conversation, test_db
        )

        # Query database for drift events
        saved_drifts = test_db.query(PersonalityDrift).filter(
            PersonalityDrift.user_id == test_personality.user_id
        ).all()

        assert len(saved_drifts) == len(drift_events)

    def test_drift_event_has_correct_data(
        self, test_db, test_personality, test_conversation
    ):
        """Test drift event contains correct data"""
        calc = PersonalityDriftCalculator()

        old_humor = test_personality.humor

        # Create conversation
        msg = Message(
            conversation_id=test_conversation.id,
            role="user",
            content="haha lol funny 😂",
        )
        test_db.add(msg)
        test_db.commit()

        # Calculate drift
        drift_events = calc.calculate_drift_after_conversation(
            test_personality, test_conversation, test_db
        )

        # Find humor drift
        humor_drifts = [d for d in drift_events if d.trait_name == "humor"]
        if humor_drifts:
            drift = humor_drifts[0]

            assert drift.user_id == test_personality.user_id
            assert drift.trait_name == "humor"
            assert drift.old_value == old_humor
            assert drift.new_value == test_personality.humor
            assert drift.change_amount == drift.new_value - drift.old_value
            assert drift.trigger_type == "conversation_pattern"
            assert drift.conversation_id == test_conversation.id
            assert drift.friendship_level == test_personality.friendship_level
            assert drift.timestamp is not None


class TestDriftReasons:
    """Test drift reasons are tracked correctly"""

    def test_drift_reasons_stored(self, test_db, test_personality, test_conversation):
        """Test drift reasons are stored in trigger_details"""
        calc = PersonalityDriftCalculator()

        # Create conversation with laughter
        for i in range(3):
            msg = Message(
                conversation_id=test_conversation.id,
                role="user",
                content="haha lol 😂",
            )
            test_db.add(msg)
        test_db.commit()

        # Calculate drift
        drift_events = calc.calculate_drift_after_conversation(
            test_personality, test_conversation, test_db
        )

        # Find humor drift and check reasons
        humor_drifts = [d for d in drift_events if d.trait_name == "humor"]
        if humor_drifts:
            drift = humor_drifts[0]
            details = drift.get_trigger_details()

            assert "reasons" in details
            assert isinstance(details["reasons"], list)
            assert len(details["reasons"]) > 0


class TestEdgeCases:
    """Test edge cases"""

    def test_empty_conversation(self, test_db, test_personality):
        """Test drift calculation with empty conversation"""
        calc = PersonalityDriftCalculator()

        # Create conversation with no messages
        conversation = Conversation(
            user_id=test_personality.user_id,
            timestamp=datetime.now(),
            message_count=0,
        )
        test_db.add(conversation)
        test_db.commit()

        # Should not crash, may not create any drifts
        drift_events = calc.calculate_drift_after_conversation(
            test_personality, conversation, test_db
        )

        # Should return empty list or small list
        assert isinstance(drift_events, list)

    def test_no_triggers_in_conversation(self, test_db, test_personality, test_conversation):
        """Test conversation with no drift triggers"""
        calc = PersonalityDriftCalculator()

        # Add neutral messages
        msg = Message(
            conversation_id=test_conversation.id,
            role="user",
            content="The weather is nice today.",
        )
        test_db.add(msg)
        test_db.commit()

        # Calculate drift
        drift_events = calc.calculate_drift_after_conversation(
            test_personality, test_conversation, test_db
        )

        # May have some minor drifts or none
        assert isinstance(drift_events, list)
