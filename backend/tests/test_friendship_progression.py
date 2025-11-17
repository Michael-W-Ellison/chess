"""
Tests for friendship progression system
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.personality import BotPersonality
from models.user import User
from database.database import Base
from services.friendship_progression import (
    FriendshipProgressionManager,
    friendship_manager,
    add_friendship_points,
    get_friendship_progress,
    get_level_info,
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


class TestFriendshipLevels:
    """Test friendship level definitions"""

    def test_all_levels_defined(self):
        """Test that all 10 levels are defined"""
        manager = FriendshipProgressionManager()
        assert len(manager.friendship_levels) == 10

    def test_level_progression(self):
        """Test that levels progress correctly"""
        manager = FriendshipProgressionManager()

        for i, level_info in enumerate(manager.friendship_levels):
            assert level_info["level"] == i + 1
            assert level_info["min_points"] >= 0
            assert level_info["name"]
            assert level_info["description"]
            assert level_info["perks"]
            assert level_info["icon"]

    def test_no_gaps_in_points(self):
        """Test that there are no gaps in point ranges"""
        manager = FriendshipProgressionManager()

        for i in range(len(manager.friendship_levels) - 1):
            current_level = manager.friendship_levels[i]
            next_level = manager.friendship_levels[i + 1]

            # Next level min should be current level max + 1
            assert next_level["min_points"] == current_level["max_points"] + 1

    def test_get_level_info(self):
        """Test getting level information"""
        manager = FriendshipProgressionManager()

        level_1 = manager.get_level_info(1)
        assert level_1["level"] == 1
        assert level_1["name"] == "Stranger"

        level_10 = manager.get_level_info(10)
        assert level_10["level"] == 10
        assert level_10["name"] == "Lifelong Companion"


class TestPointsToLevelCalculation:
    """Test points to level calculation"""

    def test_level_1_at_zero_points(self):
        """Test that 0 points equals level 1"""
        manager = FriendshipProgressionManager()
        level = manager.get_level_from_points(0)
        assert level == 1

    def test_level_2_threshold(self):
        """Test level 2 threshold"""
        manager = FriendshipProgressionManager()

        # Just below level 2
        level = manager.get_level_from_points(99)
        assert level == 1

        # At level 2
        level = manager.get_level_from_points(100)
        assert level == 2

    def test_level_10_threshold(self):
        """Test level 10 threshold"""
        manager = FriendshipProgressionManager()

        # Just below level 10
        level = manager.get_level_from_points(7499)
        assert level == 9

        # At level 10
        level = manager.get_level_from_points(7500)
        assert level == 10

        # Way above level 10
        level = manager.get_level_from_points(999999)
        assert level == 10

    def test_all_level_thresholds(self):
        """Test all level thresholds are correct"""
        manager = FriendshipProgressionManager()

        for level_info in manager.friendship_levels:
            level = level_info["level"]
            min_points = level_info["min_points"]

            calculated_level = manager.get_level_from_points(min_points)
            assert calculated_level == level


class TestPointsToNextLevel:
    """Test points needed for next level"""

    def test_points_needed_from_zero(self):
        """Test points needed starting from 0"""
        manager = FriendshipProgressionManager()

        points_needed, next_threshold = manager.get_points_to_next_level(0)
        assert points_needed == 100  # Level 2 starts at 100
        assert next_threshold == 100

    def test_points_needed_mid_level(self):
        """Test points needed from middle of a level"""
        manager = FriendshipProgressionManager()

        points_needed, next_threshold = manager.get_points_to_next_level(150)
        assert points_needed == 150  # 300 - 150 = 150 to level 3
        assert next_threshold == 300

    def test_max_level_returns_zero(self):
        """Test that max level returns 0 points needed"""
        manager = FriendshipProgressionManager()

        points_needed, next_threshold = manager.get_points_to_next_level(10000)
        assert points_needed == 0


class TestAddFriendshipPoints:
    """Test adding friendship points"""

    def test_add_points_for_message(self, test_personality, db_session):
        """Test adding points for sending a message"""
        personality, level_up, event = add_friendship_points(
            test_personality, "message_sent", db_session
        )

        assert personality.friendship_points == 5
        assert level_up is False
        assert event["points_earned"] == 5
        assert event["activity"] == "message_sent"

    def test_add_points_for_conversation(self, test_personality, db_session):
        """Test adding points for completing conversation"""
        personality, level_up, event = add_friendship_points(
            test_personality, "conversation_completed", db_session
        )

        assert personality.friendship_points == 20
        assert event["points_earned"] == 20

    def test_custom_points(self, test_personality, db_session):
        """Test adding custom points"""
        personality, level_up, event = add_friendship_points(
            test_personality, "custom_activity", db_session, custom_points=50
        )

        assert personality.friendship_points == 50
        assert event["points_earned"] == 50

    def test_unknown_activity_gives_zero(self, test_personality, db_session):
        """Test unknown activity gives 0 points"""
        personality, level_up, event = add_friendship_points(
            test_personality, "unknown_activity", db_session
        )

        assert personality.friendship_points == 0

    def test_level_up_detection(self, test_personality, db_session):
        """Test level up is detected correctly"""
        # Add 100 points to reach level 2
        personality, level_up, event = add_friendship_points(
            test_personality, "custom", db_session, custom_points=100
        )

        assert level_up is True
        assert event["level_increased"] is True
        assert event["old_level"] == 1
        assert event["new_level"] == 2
        assert "level_info" in event
        assert event["level_info"]["name"] == "Acquaintance"

    def test_multiple_points_additions(self, test_personality, db_session):
        """Test multiple point additions accumulate"""
        # Add points 5 times
        for _ in range(5):
            personality, _, _ = add_friendship_points(
                test_personality, "message_sent", db_session
            )

        assert personality.friendship_points == 25

    def test_large_point_addition(self, test_personality, db_session):
        """Test adding large number of points"""
        # Add enough points to reach level 5
        personality, level_up, event = add_friendship_points(
            test_personality, "custom", db_session, custom_points=1000
        )

        assert personality.friendship_level == 5
        assert level_up is True


class TestFriendshipProgress:
    """Test friendship progress tracking"""

    def test_progress_at_level_1(self, test_personality):
        """Test progress calculation at level 1"""
        progress = get_friendship_progress(test_personality)

        assert progress["current_level"] == 1
        assert progress["current_points"] == 0
        assert progress["points_to_next_level"] == 100
        assert progress["progress_percentage"] == 0.0
        assert progress["is_max_level"] is False

    def test_progress_mid_level(self, test_personality, db_session):
        """Test progress in middle of a level"""
        # Add 50 points (halfway to level 2)
        test_personality.friendship_points = 50
        db_session.commit()

        progress = get_friendship_progress(test_personality)

        assert progress["current_level"] == 1
        assert progress["current_points"] == 50
        assert progress["points_to_next_level"] == 50
        assert 40 < progress["progress_percentage"] < 60  # Approximately 50%

    def test_progress_at_max_level(self, test_personality, db_session):
        """Test progress at max level"""
        test_personality.friendship_points = 10000
        test_personality.friendship_level = 10
        db_session.commit()

        progress = get_friendship_progress(test_personality)

        assert progress["current_level"] == 10
        assert progress["is_max_level"] is True
        assert progress["progress_percentage"] == 100.0

    def test_progress_includes_level_info(self, test_personality):
        """Test that progress includes level information"""
        progress = get_friendship_progress(test_personality)

        assert "current_level_info" in progress
        assert progress["current_level_info"]["name"] == "Stranger"
        assert progress["current_level_info"]["description"]
        assert progress["current_level_info"]["perks"]


class TestAvailableActivities:
    """Test available activities"""

    def test_get_all_activities(self):
        """Test getting all available activities"""
        manager = FriendshipProgressionManager()
        activities = manager.get_available_activities()

        assert isinstance(activities, dict)
        assert len(activities) > 0
        assert "message_sent" in activities
        assert "conversation_completed" in activities
        assert "daily_checkin" in activities

    def test_activity_points_are_positive(self):
        """Test that all activity points are positive"""
        manager = FriendshipProgressionManager()
        activities = manager.get_available_activities()

        for activity, points in activities.items():
            assert points >= 0


class TestFriendshipHistory:
    """Test friendship history tracking"""

    def test_history_with_new_personality(self, test_personality, db_session):
        """Test history for new personality"""
        manager = FriendshipProgressionManager()
        history = manager.get_friendship_history_summary(test_personality, db_session)

        assert history["total_points_earned"] == 0
        assert history["current_level"] == 1
        assert history["total_conversations"] == 0
        assert "days_active" in history
        assert "avg_points_per_day" in history

    def test_history_with_active_user(self, test_personality, db_session):
        """Test history for active user"""
        # Simulate some activity
        test_personality.friendship_points = 500
        test_personality.friendship_level = 3
        test_personality.total_conversations = 25
        test_personality.created_at = datetime.now() - timedelta(days=10)
        db_session.commit()

        manager = FriendshipProgressionManager()
        history = manager.get_friendship_history_summary(test_personality, db_session)

        assert history["total_points_earned"] == 500
        assert history["current_level"] == 3
        assert history["total_conversations"] == 25
        assert history["days_active"] == 10
        assert history["avg_points_per_day"] == 50.0  # 500 / 10
        assert history["avg_points_per_conversation"] == 20.0  # 500 / 25


class TestSimulateLevelProgression:
    """Test level progression simulation"""

    def test_simulate_level_2(self):
        """Test simulation for level 2"""
        manager = FriendshipProgressionManager()
        simulation = manager.simulate_points_needed_for_level(2)

        assert simulation["target_level"] == 2
        assert simulation["level_name"] == "Acquaintance"
        assert simulation["points_required"] == 100
        assert "estimated_activities" in simulation

    def test_simulate_level_10(self):
        """Test simulation for level 10"""
        manager = FriendshipProgressionManager()
        simulation = manager.simulate_points_needed_for_level(10)

        assert simulation["target_level"] == 10
        assert simulation["level_name"] == "Lifelong Companion"
        assert simulation["points_required"] == 7500

    def test_simulate_invalid_level(self):
        """Test simulation with invalid level"""
        manager = FriendshipProgressionManager()

        with pytest.raises(ValueError):
            manager.simulate_points_needed_for_level(0)

        with pytest.raises(ValueError):
            manager.simulate_points_needed_for_level(11)

    def test_simulation_includes_estimates(self):
        """Test that simulation includes activity estimates"""
        manager = FriendshipProgressionManager()
        simulation = manager.simulate_points_needed_for_level(3)

        estimates = simulation["estimated_activities"]
        assert "message_sent" in estimates
        assert "conversation_completed" in estimates

        # Level 3 requires 300 points
        # message_sent gives 5 points, so should need 60 messages
        assert estimates["message_sent"] == 60.0


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_negative_points_not_allowed(self, test_personality, db_session):
        """Test that negative points don't break the system"""
        personality, level_up, event = add_friendship_points(
            test_personality, "custom", db_session, custom_points=-50
        )

        # Points shouldn't go negative (or just stay at 0)
        assert personality.friendship_points >= 0

    def test_extremely_high_points(self, test_personality, db_session):
        """Test handling extremely high points"""
        personality, level_up, event = add_friendship_points(
            test_personality, "custom", db_session, custom_points=999999
        )

        # Should cap at level 10
        assert personality.friendship_level == 10
        assert personality.friendship_points == 999999

    def test_zero_days_active(self, test_personality, db_session):
        """Test history with zero days active"""
        # Set created_at to now
        test_personality.created_at = datetime.now()
        db_session.commit()

        manager = FriendshipProgressionManager()
        history = manager.get_friendship_history_summary(test_personality, db_session)

        # Should handle division by zero
        assert history["days_active"] == 0
        assert history["avg_points_per_day"] == 0.0

    def test_zero_conversations(self, test_personality, db_session):
        """Test history with zero conversations"""
        manager = FriendshipProgressionManager()
        history = manager.get_friendship_history_summary(test_personality, db_session)

        # Should handle division by zero
        assert history["total_conversations"] == 0
        assert history["avg_points_per_conversation"] == 0.0
