"""
Tests for level-up event handling system
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.personality import BotPersonality
from models.user import User
from models.level_up_event import LevelUpEvent
from database.database import Base
from services.level_up_event_handler import (
    LevelUpEventHandler,
    level_up_event_handler,
    create_level_up_event,
    get_unacknowledged_events,
    acknowledge_event,
)
from services.friendship_progression import add_friendship_points


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


class TestLevelUpEventCreation:
    """Test creating level-up events"""

    def test_create_basic_event(self, test_user, db_session):
        """Test creating a basic level-up event"""
        event = create_level_up_event(
            user_id=test_user.id,
            old_level=1,
            new_level=2,
            friendship_points=150,
            points_earned=50,
            db=db_session
        )

        assert event.id is not None
        assert event.user_id == test_user.id
        assert event.old_level == 1
        assert event.new_level == 2
        assert event.level_name == "Acquaintance"
        assert event.friendship_points == 150
        assert event.points_earned == 50
        assert event.acknowledged is False
        assert event.celebration_message
        assert len(event.celebration_message) > 0

    def test_event_has_rewards(self, test_user, db_session):
        """Test that events include rewards"""
        event = create_level_up_event(
            user_id=test_user.id,
            old_level=2,
            new_level=3,
            friendship_points=350,
            points_earned=50,
            db=db_session
        )

        rewards = event.get_rewards()
        assert isinstance(rewards, list)
        assert len(rewards) > 0
        assert "catchphrase_unlocked" in rewards
        assert "favorites_unlocked" in rewards

    def test_event_celebration_message(self, test_user, db_session):
        """Test that celebration message is generated"""
        event = create_level_up_event(
            user_id=test_user.id,
            old_level=6,
            new_level=7,
            friendship_points=2500,
            points_earned=100,
            db=db_session
        )

        message = event.celebration_message
        assert "Best Friend" in message
        assert "🌟" in message or "💙" in message  # Contains icon
        assert "perks" in message.lower()

    def test_multiple_events_for_user(self, test_user, db_session):
        """Test creating multiple events for same user"""
        event1 = create_level_up_event(
            user_id=test_user.id,
            old_level=1,
            new_level=2,
            friendship_points=100,
            points_earned=100,
            db=db_session
        )

        event2 = create_level_up_event(
            user_id=test_user.id,
            old_level=2,
            new_level=3,
            friendship_points=300,
            points_earned=200,
            db=db_session
        )

        assert event1.id != event2.id
        assert event1.new_level == 2
        assert event2.new_level == 3


class TestEventAcknowledgement:
    """Test acknowledging events"""

    def test_acknowledge_event(self, test_user, db_session):
        """Test marking event as acknowledged"""
        event = create_level_up_event(
            user_id=test_user.id,
            old_level=1,
            new_level=2,
            friendship_points=100,
            points_earned=100,
            db=db_session
        )

        assert event.acknowledged is False
        assert event.acknowledged_at is None

        updated_event = acknowledge_event(event.id, db_session)

        assert updated_event.acknowledged is True
        assert updated_event.acknowledged_at is not None

    def test_get_unacknowledged_events(self, test_user, db_session):
        """Test getting unacknowledged events"""
        # Create multiple events
        event1 = create_level_up_event(
            user_id=test_user.id,
            old_level=1,
            new_level=2,
            friendship_points=100,
            points_earned=100,
            db=db_session
        )

        event2 = create_level_up_event(
            user_id=test_user.id,
            old_level=2,
            new_level=3,
            friendship_points=300,
            points_earned=200,
            db=db_session
        )

        # Both should be unacknowledged
        unack = get_unacknowledged_events(test_user.id, db_session)
        assert len(unack) == 2

        # Acknowledge one
        acknowledge_event(event1.id, db_session)

        # Should only have one unacknowledged
        unack = get_unacknowledged_events(test_user.id, db_session)
        assert len(unack) == 1
        assert unack[0].id == event2.id

    def test_acknowledge_all_events(self, test_user, db_session):
        """Test acknowledging all events at once"""
        handler = LevelUpEventHandler()

        # Create multiple events
        for i in range(3):
            create_level_up_event(
                user_id=test_user.id,
                old_level=i + 1,
                new_level=i + 2,
                friendship_points=(i + 2) * 100,
                points_earned=100,
                db=db_session
            )

        # All should be unacknowledged
        unack = handler.get_unacknowledged_events(test_user.id, db_session)
        assert len(unack) == 3

        # Acknowledge all
        count = handler.acknowledge_all_events(test_user.id, db_session)
        assert count == 3

        # None should be unacknowledged
        unack = handler.get_unacknowledged_events(test_user.id, db_session)
        assert len(unack) == 0


class TestEventHistory:
    """Test event history retrieval"""

    def test_get_event_history(self, test_user, db_session):
        """Test getting event history"""
        handler = LevelUpEventHandler()

        # Create events
        for i in range(5):
            create_level_up_event(
                user_id=test_user.id,
                old_level=i + 1,
                new_level=i + 2,
                friendship_points=(i + 2) * 100,
                points_earned=100,
                db=db_session
            )

        # Get all history
        history = handler.get_event_history(test_user.id, db_session)
        assert len(history) == 5

        # Get limited history
        limited = handler.get_event_history(test_user.id, db_session, limit=2)
        assert len(limited) == 2

        # Most recent should be first
        assert limited[0].new_level > limited[1].new_level

    def test_event_summary(self, test_user, db_session):
        """Test getting event summary"""
        handler = LevelUpEventHandler()

        # Create some events
        create_level_up_event(
            user_id=test_user.id,
            old_level=1,
            new_level=2,
            friendship_points=100,
            points_earned=100,
            db=db_session
        )

        event2 = create_level_up_event(
            user_id=test_user.id,
            old_level=2,
            new_level=3,
            friendship_points=300,
            points_earned=200,
            db=db_session
        )

        summary = handler.get_event_summary(test_user.id, db_session)

        assert summary["total_level_ups"] == 2
        assert summary["unacknowledged_count"] == 2
        assert summary["latest_level_up"]["new_level"] == 3
        assert summary["total_rewards_unlocked"] > 0


class TestCelebrationCheck:
    """Test celebration checking"""

    def test_should_show_celebration_with_unacked(self, test_user, db_session):
        """Test celebration check with unacknowledged events"""
        handler = LevelUpEventHandler()

        event = create_level_up_event(
            user_id=test_user.id,
            old_level=1,
            new_level=2,
            friendship_points=100,
            points_earned=100,
            db=db_session
        )

        should_show, event_to_show = handler.should_show_celebration(test_user.id, db_session)

        assert should_show is True
        assert event_to_show is not None
        assert event_to_show.id == event.id

    def test_should_not_show_celebration_when_acked(self, test_user, db_session):
        """Test celebration check with all events acknowledged"""
        handler = LevelUpEventHandler()

        event = create_level_up_event(
            user_id=test_user.id,
            old_level=1,
            new_level=2,
            friendship_points=100,
            points_earned=100,
            db=db_session
        )

        # Acknowledge event
        handler.acknowledge_event(event.id, db_session)

        should_show, event_to_show = handler.should_show_celebration(test_user.id, db_session)

        assert should_show is False
        assert event_to_show is None

    def test_shows_oldest_unacknowledged(self, test_user, db_session):
        """Test that oldest unacknowledged event is shown"""
        handler = LevelUpEventHandler()

        event1 = create_level_up_event(
            user_id=test_user.id,
            old_level=1,
            new_level=2,
            friendship_points=100,
            points_earned=100,
            db=db_session
        )

        event2 = create_level_up_event(
            user_id=test_user.id,
            old_level=2,
            new_level=3,
            friendship_points=300,
            points_earned=200,
            db=db_session
        )

        should_show, event_to_show = handler.should_show_celebration(test_user.id, db_session)

        # Should show oldest (event1)
        assert event_to_show.id == event1.id


class TestRewards:
    """Test reward system"""

    def test_get_level_rewards(self):
        """Test getting rewards for specific levels"""
        handler = LevelUpEventHandler()

        # Level 1 has no rewards
        rewards_1 = handler.get_level_rewards(1)
        assert len(rewards_1) == 0

        # Level 3 has catchphrase and favorites
        rewards_3 = handler.get_level_rewards(3)
        assert "catchphrase_unlocked" in rewards_3
        assert "favorites_unlocked" in rewards_3

        # Level 10 has all features
        rewards_10 = handler.get_level_rewards(10)
        assert "all_features_unlocked" in rewards_10
        assert "legacy_memories" in rewards_10

    def test_get_all_rewards(self):
        """Test getting all level rewards"""
        handler = LevelUpEventHandler()

        all_rewards = handler.get_all_level_rewards()

        assert isinstance(all_rewards, dict)
        assert len(all_rewards) == 10
        assert 1 in all_rewards
        assert 10 in all_rewards


class TestIntegrationWithFriendship:
    """Test integration with friendship progression"""

    def test_level_up_creates_event(self, test_personality, db_session):
        """Test that leveling up automatically creates an event"""
        handler = LevelUpEventHandler()

        # Add enough points to level up from 1 to 2
        _, level_increased, _ = add_friendship_points(
            test_personality,
            "custom",
            db_session,
            custom_points=100
        )

        assert level_increased is True
        assert test_personality.friendship_level == 2

        # Check that event was created
        events = handler.get_event_history(test_personality.user_id, db_session)
        assert len(events) == 1
        assert events[0].old_level == 1
        assert events[0].new_level == 2

    def test_multiple_level_ups_create_multiple_events(self, test_personality, db_session):
        """Test that multiple level-ups create multiple events"""
        handler = LevelUpEventHandler()

        # Level up to 2
        add_friendship_points(test_personality, "custom", db_session, custom_points=100)

        # Level up to 3
        add_friendship_points(test_personality, "custom", db_session, custom_points=200)

        # Check that both events were created
        events = handler.get_event_history(test_personality.user_id, db_session)
        assert len(events) == 2
        assert events[0].new_level == 3  # Most recent first
        assert events[1].new_level == 2

    def test_no_event_when_no_level_up(self, test_personality, db_session):
        """Test that no event is created when not leveling up"""
        handler = LevelUpEventHandler()

        # Add points but don't level up
        add_friendship_points(test_personality, "message_sent", db_session)

        # No events should be created
        events = handler.get_event_history(test_personality.user_id, db_session)
        assert len(events) == 0


class TestEventModel:
    """Test LevelUpEvent model"""

    def test_to_dict(self, test_user, db_session):
        """Test event to_dict conversion"""
        event = create_level_up_event(
            user_id=test_user.id,
            old_level=1,
            new_level=2,
            friendship_points=100,
            points_earned=100,
            db=db_session
        )

        data = event.to_dict()

        assert data["id"] == event.id
        assert data["user_id"] == test_user.id
        assert data["old_level"] == 1
        assert data["new_level"] == 2
        assert data["level_name"] == "Acquaintance"
        assert data["friendship_points"] == 100
        assert data["points_earned"] == 100
        assert "timestamp" in data
        assert "celebration_message" in data
        assert "rewards" in data
        assert data["acknowledged"] is False

    def test_rewards_json(self, test_user, db_session):
        """Test rewards are properly stored as JSON"""
        event = LevelUpEvent(
            user_id=test_user.id,
            old_level=1,
            new_level=2,
            level_name="Test",
            friendship_points=100,
            points_earned=100,
            celebration_message="Test",
        )

        rewards = ["reward1", "reward2", "reward3"]
        event.set_rewards(rewards)

        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)

        retrieved_rewards = event.get_rewards()
        assert retrieved_rewards == rewards


class TestEdgeCases:
    """Test edge cases"""

    def test_acknowledge_nonexistent_event(self, db_session):
        """Test acknowledging non-existent event"""
        result = acknowledge_event(99999, db_session)
        assert result is None

    def test_empty_event_history(self, test_user, db_session):
        """Test getting history with no events"""
        handler = LevelUpEventHandler()

        history = handler.get_event_history(test_user.id, db_session)
        assert len(history) == 0

        summary = handler.get_event_summary(test_user.id, db_session)
        assert summary["total_level_ups"] == 0
        assert summary["unacknowledged_count"] == 0
        assert summary["latest_level_up"] is None

    def test_max_level_rewards(self):
        """Test that max level (10) has rewards"""
        handler = LevelUpEventHandler()

        rewards = handler.get_level_rewards(10)
        assert len(rewards) > 0
        assert "all_features_unlocked" in rewards
