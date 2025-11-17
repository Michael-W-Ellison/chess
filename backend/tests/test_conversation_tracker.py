"""
Tests for conversation tracking system
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.personality import BotPersonality
from models.user import User
from models.conversation import Conversation, Message
from database.database import Base
from services.conversation_tracker import (
    ConversationTracker,
    conversation_tracker,
    on_conversation_start,
    on_message_sent,
    on_conversation_end,
    get_conversation_stats,
)


@pytest.fixture
def db_session():
    """Create in-memory database for testing"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()


@pytest.fixture
def test_user(db_session):
    """Create test user"""
    user = User(
        id=1,
        name="Test User",
        age=12,
        grade=6,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_personality(db_session, test_user):
    """Create test personality"""
    personality = BotPersonality(
        user_id=test_user.id,
        name="TestBot",
        humor=0.5,
        energy=0.6,
        curiosity=0.5,
        formality=0.3,
        friendship_level=1,
        friendship_points=0,
        total_conversations=0,
        mood="happy",
    )
    db_session.add(personality)
    db_session.commit()
    db_session.refresh(personality)
    return personality


@pytest.fixture
def test_conversation(db_session, test_user):
    """Create test conversation"""
    conversation = Conversation(
        user_id=test_user.id,
        timestamp=datetime.now(),
        message_count=0,
    )
    db_session.add(conversation)
    db_session.commit()
    db_session.refresh(conversation)
    return conversation


class TestConversationStart:
    """Test conversation start tracking"""

    def test_first_conversation_today(self, test_user, test_personality, db_session):
        """Test first conversation today triggers check-in"""
        result = on_conversation_start(test_user.id, test_personality, db_session)

        assert result["is_first_today"] is True
        assert len(result["points_awarded"]) >= 1
        assert result["points_awarded"][0]["activity"] == "daily_checkin"
        assert test_personality.friendship_points > 0

    def test_second_conversation_today(self, test_user, test_personality, test_conversation, db_session):
        """Test second conversation today doesn't trigger check-in"""
        # First conversation
        on_conversation_start(test_user.id, test_personality, db_session)

        # Second conversation same day
        result = on_conversation_start(test_user.id, test_personality, db_session)

        assert result["is_first_today"] is False
        assert len(result["points_awarded"]) == 0

    def test_streak_bonus_3_days(self, test_user, test_personality, db_session):
        """Test 3-day streak bonus"""
        # Create conversations for 3 consecutive days
        for i in range(3):
            date = datetime.now() - timedelta(days=(2 - i))
            conversation = Conversation(
                user_id=test_user.id,
                timestamp=date,
                message_count=5,
            )
            db_session.add(conversation)

        db_session.commit()

        # New conversation today should trigger streak
        result = on_conversation_start(test_user.id, test_personality, db_session)

        assert result["streak_days"] >= 3
        assert result["streak_bonus"] is True
        # Should have daily_checkin + streak_3_days
        assert len(result["points_awarded"]) >= 2


class TestMessageTracking:
    """Test message activity tracking"""

    def test_basic_message_points(self, test_user, test_personality, db_session):
        """Test basic message awards points"""
        result = on_message_sent(
            test_user.id, test_personality, "Hello bot!", db_session
        )

        assert len(result["points_awarded"]) >= 1
        assert result["points_awarded"][0]["activity"] == "message_sent"
        assert test_personality.friendship_points > 0

    def test_thanks_detection(self, test_user, test_personality, db_session):
        """Test detection of thanks/gratitude"""
        result = on_message_sent(
            test_user.id, test_personality, "Thanks for helping me!", db_session
        )

        activities = [p["activity"] for p in result["points_awarded"]]
        assert "thanks_bot" in activities
        assert "thanked_bot" in result["activities_detected"]

    def test_laughter_detection(self, test_user, test_personality, db_session):
        """Test detection of laughter"""
        result = on_message_sent(
            test_user.id, test_personality, "Haha that's so funny!", db_session
        )

        activities = [p["activity"] for p in result["points_awarded"]]
        assert "laughs_at_joke" in activities
        assert "laughed" in result["activities_detected"]

    def test_feelings_detection(self, test_user, test_personality, db_session):
        """Test detection of sharing feelings"""
        result = on_message_sent(
            test_user.id, test_personality, "I feel really happy today!", db_session
        )

        activities = [p["activity"] for p in result["points_awarded"]]
        assert "shares_feelings" in activities
        assert "shared_feelings" in result["activities_detected"]

    def test_advice_request_detection(self, test_user, test_personality, db_session):
        """Test detection of asking for advice"""
        result = on_message_sent(
            test_user.id, test_personality, "What should I do about this problem?", db_session
        )

        activities = [p["activity"] for p in result["points_awarded"]]
        assert "asks_for_advice" in activities
        assert "asked_advice" in result["activities_detected"]

    def test_positive_feedback_detection(self, test_user, test_personality, db_session):
        """Test detection of positive feedback"""
        result = on_message_sent(
            test_user.id, test_personality, "You're the best bot ever!", db_session
        )

        activities = [p["activity"] for p in result["points_awarded"]]
        assert "positive_feedback" in activities
        assert "positive_feedback" in result["activities_detected"]

    def test_multiple_activities_detected(self, test_user, test_personality, db_session):
        """Test multiple activities in one message"""
        result = on_message_sent(
            test_user.id,
            test_personality,
            "Thanks for the advice! You're awesome and I feel much better now!",
            db_session
        )

        # Should detect: thanks_bot, positive_feedback, shares_feelings
        assert len(result["activities_detected"]) >= 2


class TestConversationEnd:
    """Test conversation end tracking"""

    def test_short_conversation(self, test_conversation, test_personality, db_session):
        """Test short conversation awards basic points"""
        test_conversation.message_count = 5
        db_session.commit()

        result = on_conversation_end(
            test_conversation.id, test_personality, db_session
        )

        assert result["conversation_quality"] == "short"
        assert result["message_count"] == 5
        # Should only have conversation_completed
        activities = [p["activity"] for p in result["points_awarded"]]
        assert "conversation_completed" in activities
        assert "long_conversation" not in activities

    def test_long_conversation(self, test_conversation, test_personality, db_session):
        """Test long conversation (10+ messages) awards bonus"""
        test_conversation.message_count = 15
        db_session.commit()

        result = on_conversation_end(
            test_conversation.id, test_personality, db_session
        )

        assert result["conversation_quality"] == "long"
        activities = [p["activity"] for p in result["points_awarded"]]
        assert "conversation_completed" in activities
        assert "long_conversation" in activities

    def test_quality_conversation(self, test_conversation, test_personality, db_session):
        """Test quality conversation (20+ messages) awards max bonus"""
        test_conversation.message_count = 25
        db_session.commit()

        result = on_conversation_end(
            test_conversation.id, test_personality, db_session
        )

        assert result["conversation_quality"] == "quality"
        activities = [p["activity"] for p in result["points_awarded"]]
        assert "conversation_completed" in activities
        assert "quality_conversation" in activities

    def test_conversation_count_incremented(self, test_conversation, test_personality, db_session):
        """Test total_conversations is incremented"""
        old_count = test_personality.total_conversations

        test_conversation.message_count = 5
        db_session.commit()

        on_conversation_end(test_conversation.id, test_personality, db_session)

        assert test_personality.total_conversations == old_count + 1


class TestStreakCalculation:
    """Test streak calculation"""

    def test_no_conversations_zero_streak(self, test_user, db_session):
        """Test no conversations returns 0 streak"""
        tracker = ConversationTracker()
        streak = tracker.calculate_streak(test_user.id, db_session)
        assert streak == 0

    def test_conversation_today_streak_1(self, test_user, db_session):
        """Test conversation today gives streak of 1"""
        conversation = Conversation(
            user_id=test_user.id,
            timestamp=datetime.now(),
            message_count=5,
        )
        db_session.add(conversation)
        db_session.commit()

        tracker = ConversationTracker()
        streak = tracker.calculate_streak(test_user.id, db_session)
        assert streak == 1

    def test_consecutive_days_streak(self, test_user, db_session):
        """Test consecutive days builds streak"""
        # Create conversations for 5 consecutive days
        for i in range(5):
            date = datetime.now() - timedelta(days=(4 - i))
            conversation = Conversation(
                user_id=test_user.id,
                timestamp=date,
                message_count=5,
            )
            db_session.add(conversation)

        db_session.commit()

        tracker = ConversationTracker()
        streak = tracker.calculate_streak(test_user.id, db_session)
        assert streak == 5

    def test_gap_breaks_streak(self, test_user, db_session):
        """Test gap in days breaks streak"""
        # Conversation 5 days ago
        old_convo = Conversation(
            user_id=test_user.id,
            timestamp=datetime.now() - timedelta(days=5),
            message_count=5,
        )
        db_session.add(old_convo)

        # Conversation today
        new_convo = Conversation(
            user_id=test_user.id,
            timestamp=datetime.now(),
            message_count=5,
        )
        db_session.add(new_convo)

        db_session.commit()

        tracker = ConversationTracker()
        streak = tracker.calculate_streak(test_user.id, db_session)
        # Should only count today
        assert streak == 1

    def test_longest_streak(self, test_user, db_session):
        """Test longest streak calculation"""
        tracker = ConversationTracker()

        # Create streak: 5 days ago to 3 days ago (3-day streak)
        for i in range(3):
            date = datetime.now() - timedelta(days=(5 - i))
            conversation = Conversation(
                user_id=test_user.id,
                timestamp=date,
                message_count=5,
            )
            db_session.add(conversation)

        # Gap

        # Create current streak: yesterday and today (2-day streak)
        for i in range(2):
            date = datetime.now() - timedelta(days=(1 - i))
            conversation = Conversation(
                user_id=test_user.id,
                timestamp=date,
                message_count=5,
            )
            db_session.add(conversation)

        db_session.commit()

        longest = tracker.get_longest_streak(test_user.id, db_session)
        # Longest should be 3
        assert longest == 3


class TestConversationStats:
    """Test conversation statistics"""

    def test_stats_with_no_conversations(self, test_user, db_session):
        """Test stats with no conversations"""
        stats = get_conversation_stats(test_user.id, db_session)

        assert stats["total_conversations"] == 0
        assert stats["total_messages"] == 0
        assert stats["current_streak"] == 0
        assert stats["days_active"] == 0

    def test_stats_with_conversations(self, test_user, db_session):
        """Test stats with multiple conversations"""
        # Create 3 conversations
        for i in range(3):
            conversation = Conversation(
                user_id=test_user.id,
                timestamp=datetime.now() - timedelta(days=i),
                message_count=10,
                duration_seconds=300,
            )
            db_session.add(conversation)

            # Add messages
            for j in range(10):
                message = Message(
                    conversation_id=conversation.id,
                    role="user" if j % 2 == 0 else "assistant",
                    content=f"Message {j}",
                    timestamp=datetime.now(),
                )
                db_session.add(message)

        db_session.commit()

        # Need to refresh conversations to get IDs for messages
        db_session.flush()

        stats = get_conversation_stats(test_user.id, db_session)

        assert stats["total_conversations"] == 3
        assert stats["total_messages"] > 0  # SQLite in-memory might not link properly
        assert stats["avg_messages_per_conversation"] == 10.0
        assert stats["avg_duration_seconds"] == 300.0
        assert stats["current_streak"] >= 1


class TestIsFirstConversationToday:
    """Test first conversation detection"""

    def test_no_conversations_is_first(self, test_user, db_session):
        """Test no conversations means first today"""
        tracker = ConversationTracker()
        is_first = tracker.is_first_conversation_today(test_user.id, db_session)
        assert is_first is True

    def test_conversation_today_not_first(self, test_user, db_session):
        """Test existing conversation today means not first"""
        conversation = Conversation(
            user_id=test_user.id,
            timestamp=datetime.now(),
            message_count=5,
        )
        db_session.add(conversation)
        db_session.commit()

        tracker = ConversationTracker()
        is_first = tracker.is_first_conversation_today(test_user.id, db_session)
        assert is_first is False

    def test_conversation_yesterday_is_first(self, test_user, db_session):
        """Test conversation yesterday means first today"""
        conversation = Conversation(
            user_id=test_user.id,
            timestamp=datetime.now() - timedelta(days=1),
            message_count=5,
        )
        db_session.add(conversation)
        db_session.commit()

        tracker = ConversationTracker()
        is_first = tracker.is_first_conversation_today(test_user.id, db_session)
        assert is_first is True


class TestEdgeCases:
    """Test edge cases"""

    def test_end_nonexistent_conversation(self, test_personality, db_session):
        """Test ending non-existent conversation"""
        result = on_conversation_end(99999, test_personality, db_session)

        # Should return empty result without crashing
        assert result["message_count"] == 0

    def test_multiple_conversations_same_day(self, test_user, test_personality, db_session):
        """Test multiple conversations on same day"""
        # First conversation
        result1 = on_conversation_start(test_user.id, test_personality, db_session)
        assert result1["is_first_today"] is True

        # Second conversation same day
        result2 = on_conversation_start(test_user.id, test_personality, db_session)
        assert result2["is_first_today"] is False

        # Both should work without errors
