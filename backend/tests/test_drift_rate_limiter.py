"""
Tests for Drift Rate Limiter
Tests rate limiting on personality trait drift
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.database import Base
from models.user import User
from models.personality import BotPersonality
from models.personality_drift import PersonalityDrift
from services.drift_rate_limiter import DriftRateLimiter, drift_rate_limiter


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
    """Create test personality"""
    personality = BotPersonality(
        user_id=test_user.id,
        name="TestBot",
        humor=0.5,
        energy=0.6,
        curiosity=0.5,
        formality=0.3,
        friendship_level=3,
        mood="happy",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    test_db.add(personality)
    test_db.commit()
    test_db.refresh(personality)
    return personality


class TestRateLimiterInitialization:
    """Test rate limiter initialization"""

    def test_limiter_constants(self):
        """Test limiter has correct constants"""
        limiter = DriftRateLimiter()

        assert limiter.MAX_DRIFT_PER_CONVERSATION == 0.02
        assert limiter.MAX_DRIFT_PER_DAY == 0.05
        assert limiter.MAX_DRIFT_PER_WEEK == 0.10
        assert limiter.MAX_DRIFT_PER_MONTH == 0.15
        assert limiter.LARGE_DRIFT_THRESHOLD == 0.04


class TestConversationLimit:
    """Test per-conversation drift limits"""

    def test_within_conversation_limit(self, test_db, test_personality):
        """Test drift within per-conversation limit is allowed"""
        limiter = DriftRateLimiter()

        allowed, capped, msg = limiter.check_conversation_limit(
            test_personality, "humor", 0.01, test_db
        )

        assert allowed is True
        assert capped == 0.01
        assert "Within" in msg

    def test_exceeds_conversation_limit(self, test_db, test_personality):
        """Test drift exceeding per-conversation limit is capped"""
        limiter = DriftRateLimiter()

        allowed, capped, msg = limiter.check_conversation_limit(
            test_personality, "humor", 0.05, test_db  # Exceeds 0.02 limit
        )

        assert allowed is False
        assert capped == 0.02  # Capped to limit
        assert "capped" in msg.lower()

    def test_negative_drift_capped(self, test_db, test_personality):
        """Test negative drift is also capped"""
        limiter = DriftRateLimiter()

        allowed, capped, msg = limiter.check_conversation_limit(
            test_personality, "humor", -0.05, test_db
        )

        assert allowed is False
        assert capped == -0.02  # Capped to negative limit


class TestTimePeriodLimit:
    """Test time period drift limits"""

    def test_within_monthly_limit(self, test_db, test_personality):
        """Test drift within monthly limit is allowed"""
        limiter = DriftRateLimiter()

        allowed, capped, msg = limiter.check_time_period_limit(
            test_personality, "humor", 0.05, test_db, period_days=30
        )

        assert allowed is True
        assert capped == 0.05
        assert "30-day limit" in msg

    def test_exceeds_monthly_limit_with_history(self, test_db, test_personality):
        """Test drift exceeds limit when combined with history"""
        limiter = DriftRateLimiter()

        # Add drift events totaling 0.12 in the last month
        for i in range(4):
            drift = PersonalityDrift(
                user_id=test_personality.user_id,
                trait_name="humor",
                old_value=0.5,
                new_value=0.53,
                change_amount=0.03,
                trigger_type="conversation_pattern",
                friendship_level=3,
                timestamp=datetime.now() - timedelta(days=i*5)
            )
            test_db.add(drift)
        test_db.commit()

        # Try to add 0.05 more (would total 0.17, exceeds 0.15 limit)
        allowed, capped, msg = limiter.check_time_period_limit(
            test_personality, "humor", 0.05, test_db, period_days=30
        )

        assert allowed is False
        assert capped < 0.05  # Should be capped to remaining allowance
        assert "capped" in msg.lower()

    def test_daily_limit(self, test_db, test_personality):
        """Test daily drift limit"""
        limiter = DriftRateLimiter()

        # Add drift event today
        drift = PersonalityDrift(
            user_id=test_personality.user_id,
            trait_name="humor",
            old_value=0.5,
            new_value=0.54,
            change_amount=0.04,
            trigger_type="conversation_pattern",
            friendship_level=3,
            timestamp=datetime.now()
        )
        test_db.add(drift)
        test_db.commit()

        # Try to add more (daily limit is 0.05)
        allowed, capped, msg = limiter.check_time_period_limit(
            test_personality, "humor", 0.03, test_db, period_days=1
        )

        assert allowed is False
        # Should allow only remaining 0.01
        assert capped <= 0.01


class TestCooldown:
    """Test cooldown after large drifts"""

    def test_no_cooldown_no_recent_drift(self, test_db, test_personality):
        """Test no cooldown when no recent large drift"""
        limiter = DriftRateLimiter()

        in_cooldown, until, msg = limiter.check_cooldown(
            test_personality, "humor", test_db
        )

        assert in_cooldown is False
        assert until is None
        assert "No cooldown" in msg

    def test_cooldown_after_large_drift(self, test_db, test_personality):
        """Test cooldown is active after large drift"""
        limiter = DriftRateLimiter()

        # Add large drift 1 hour ago
        drift = PersonalityDrift(
            user_id=test_personality.user_id,
            trait_name="humor",
            old_value=0.5,
            new_value=0.55,
            change_amount=0.05,  # Above 0.04 threshold
            trigger_type="conversation_pattern",
            friendship_level=3,
            timestamp=datetime.now() - timedelta(hours=1)
        )
        test_db.add(drift)
        test_db.commit()

        in_cooldown, until, msg = limiter.check_cooldown(
            test_personality, "humor", test_db
        )

        assert in_cooldown is True
        assert until is not None
        assert "cooldown" in msg.lower()

    def test_cooldown_expired(self, test_db, test_personality):
        """Test cooldown expires after time period"""
        limiter = DriftRateLimiter()

        # Add large drift 7 hours ago (cooldown is 6 hours)
        drift = PersonalityDrift(
            user_id=test_personality.user_id,
            trait_name="humor",
            old_value=0.5,
            new_value=0.55,
            change_amount=0.05,
            trigger_type="conversation_pattern",
            friendship_level=3,
            timestamp=datetime.now() - timedelta(hours=7)
        )
        test_db.add(drift)
        test_db.commit()

        in_cooldown, until, msg = limiter.check_cooldown(
            test_personality, "humor", test_db
        )

        assert in_cooldown is False
        assert "expired" in msg.lower()


class TestApplyRateLimits:
    """Test applying all rate limits together"""

    def test_no_limits_applied(self, test_db, test_personality):
        """Test when no limits need to be applied"""
        limiter = DriftRateLimiter()

        final_drift, messages = limiter.apply_rate_limits(
            test_personality, "humor", 0.01, test_db
        )

        assert final_drift == 0.01
        assert len(messages) == 0

    def test_conversation_limit_applied(self, test_db, test_personality):
        """Test conversation limit is applied"""
        limiter = DriftRateLimiter()

        final_drift, messages = limiter.apply_rate_limits(
            test_personality, "humor", 0.05, test_db
        )

        assert final_drift == 0.02  # Capped to conversation limit
        assert len(messages) > 0

    def test_cooldown_blocks_drift(self, test_db, test_personality):
        """Test cooldown blocks all drift"""
        limiter = DriftRateLimiter()

        # Add recent large drift
        drift = PersonalityDrift(
            user_id=test_personality.user_id,
            trait_name="humor",
            old_value=0.5,
            new_value=0.55,
            change_amount=0.05,
            trigger_type="conversation_pattern",
            friendship_level=3,
            timestamp=datetime.now() - timedelta(hours=1)
        )
        test_db.add(drift)
        test_db.commit()

        final_drift, messages = limiter.apply_rate_limits(
            test_personality, "humor", 0.02, test_db, enforce_cooldown=True
        )

        assert final_drift == 0.0  # Blocked by cooldown
        assert any("cooldown" in msg.lower() for msg in messages)


class TestDriftAllowance:
    """Test drift allowance calculations"""

    def test_full_allowance_no_history(self, test_db, test_personality):
        """Test full allowance when no drift history"""
        limiter = DriftRateLimiter()

        allowance = limiter.get_drift_allowance(
            test_personality, "humor", test_db, period_days=30
        )

        assert allowance["period_days"] == 30
        assert allowance["max_drift"] == 0.15
        assert allowance["used_drift"] == 0.0
        assert allowance["remaining_drift"] == 0.15
        assert allowance["usage_percentage"] == 0.0
        assert allowance["can_drift"] is True

    def test_partial_allowance_with_history(self, test_db, test_personality):
        """Test partial allowance when some drift has occurred"""
        limiter = DriftRateLimiter()

        # Add drift events
        drift = PersonalityDrift(
            user_id=test_personality.user_id,
            trait_name="humor",
            old_value=0.5,
            new_value=0.55,
            change_amount=0.05,
            trigger_type="conversation_pattern",
            friendship_level=3,
            timestamp=datetime.now()
        )
        test_db.add(drift)
        test_db.commit()

        allowance = limiter.get_drift_allowance(
            test_personality, "humor", test_db, period_days=30
        )

        assert allowance["used_drift"] == 0.05
        assert allowance["remaining_drift"] == 0.10  # 0.15 - 0.05
        assert allowance["usage_percentage"] > 0


class TestGetAllAllowances:
    """Test getting all allowances for a trait"""

    def test_all_allowances(self, test_db, test_personality):
        """Test getting daily, weekly, monthly allowances"""
        limiter = DriftRateLimiter()

        allowances = limiter.get_all_allowances(
            test_personality, "humor", test_db
        )

        assert allowances["trait_name"] == "humor"
        assert "daily" in allowances
        assert "weekly" in allowances
        assert "monthly" in allowances
        assert allowances["per_conversation_limit"] == 0.02

        # Check daily allowance
        assert allowances["daily"]["max_drift"] == 0.05
        assert allowances["daily"]["period_days"] == 1

        # Check weekly allowance
        assert allowances["weekly"]["max_drift"] == 0.10
        assert allowances["weekly"]["period_days"] == 7

        # Check monthly allowance
        assert allowances["monthly"]["max_drift"] == 0.15
        assert allowances["monthly"]["period_days"] == 30


class TestDriftRateStats:
    """Test drift rate statistics"""

    def test_stats_for_all_traits(self, test_db, test_personality):
        """Test getting stats for all traits"""
        limiter = DriftRateLimiter()

        stats = limiter.get_drift_rate_stats(test_personality, test_db)

        assert stats["user_id"] == test_personality.user_id
        assert "traits" in stats
        assert len(stats["traits"]) == 4  # All 4 traits

        # Check each trait has required info
        for trait in ["humor", "energy", "curiosity", "formality"]:
            assert trait in stats["traits"]
            assert "allowances" in stats["traits"][trait]
            assert "in_cooldown" in stats["traits"][trait]


class TestGlobalInstance:
    """Test global drift_rate_limiter instance"""

    def test_global_instance_exists(self):
        """Test global instance is accessible"""
        assert drift_rate_limiter is not None
        assert isinstance(drift_rate_limiter, DriftRateLimiter)

    def test_global_instance_convenience_functions(self, test_db, test_personality):
        """Test convenience functions use global instance"""
        from services.drift_rate_limiter import (
            apply_rate_limits,
            get_drift_allowance,
            get_drift_rate_stats,
        )

        # Test apply_rate_limits
        final_drift, messages = apply_rate_limits(
            test_personality, "humor", 0.01, test_db
        )
        assert final_drift == 0.01

        # Test get_drift_allowance
        allowance = get_drift_allowance(test_personality, "humor", test_db)
        assert "max_drift" in allowance

        # Test get_drift_rate_stats
        stats = get_drift_rate_stats(test_personality, test_db)
        assert "traits" in stats


class TestEdgeCases:
    """Test edge cases"""

    def test_zero_drift_request(self, test_db, test_personality):
        """Test requesting zero drift"""
        limiter = DriftRateLimiter()

        final_drift, messages = limiter.apply_rate_limits(
            test_personality, "humor", 0.0, test_db
        )

        assert final_drift == 0.0

    def test_multiple_traits_independent_limits(self, test_db, test_personality):
        """Test each trait has independent rate limits"""
        limiter = DriftRateLimiter()

        # Add max drift for humor
        drift = PersonalityDrift(
            user_id=test_personality.user_id,
            trait_name="humor",
            old_value=0.5,
            new_value=0.52,
            change_amount=0.02,
            trigger_type="conversation_pattern",
            friendship_level=3,
            timestamp=datetime.now()
        )
        test_db.add(drift)
        test_db.commit()

        # Energy should still have full allowance
        allowance_humor = limiter.get_drift_allowance(
            test_personality, "humor", test_db, 1
        )
        allowance_energy = limiter.get_drift_allowance(
            test_personality, "energy", test_db, 1
        )

        assert allowance_humor["used_drift"] > 0
        assert allowance_energy["used_drift"] == 0
