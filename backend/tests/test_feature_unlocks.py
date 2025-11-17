"""
Tests for feature unlock system
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.personality import BotPersonality
from models.user import User
from database.database import Base
from services.feature_unlock_manager import (
    FeatureUnlockManager,
    feature_unlock_manager,
    is_feature_unlocked,
    get_unlocked_features,
    get_feature_summary,
)
from services.feature_gates import (
    FeatureNotUnlockedException,
    require_feature,
    check_feature_access,
    get_feature_gate_message,
    can_use_catchphrase,
    can_give_advice,
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
def test_personality_level_1(db_session, test_user):
    """Create test personality at level 1"""
    personality = BotPersonality(
        user_id=test_user.id,
        name="TestBot",
        friendship_level=1,
        friendship_points=0,
    )
    db_session.add(personality)
    db_session.commit()
    db_session.refresh(personality)
    return personality


@pytest.fixture
def test_personality_level_5(db_session, test_user):
    """Create test personality at level 5"""
    personality = BotPersonality(
        user_id=test_user.id,
        name="TestBot",
        friendship_level=5,
        friendship_points=1200,
    )
    db_session.add(personality)
    db_session.commit()
    db_session.refresh(personality)
    return personality


@pytest.fixture
def test_personality_level_10(db_session, test_user):
    """Create test personality at level 10"""
    personality = BotPersonality(
        user_id=test_user.id,
        name="TestBot",
        friendship_level=10,
        friendship_points=8000,
    )
    db_session.add(personality)
    db_session.commit()
    db_session.refresh(personality)
    return personality


class TestFeatureUnlockManager:
    """Test feature unlock manager"""

    def test_feature_definitions_exist(self):
        """Test that all features are defined"""
        manager = FeatureUnlockManager()

        assert len(manager.feature_definitions) > 0
        assert "basic_chat" in manager.feature_definitions
        assert "catchphrase_unlocked" in manager.feature_definitions
        assert "max_personalization" in manager.feature_definitions

    def test_all_features_have_required_fields(self):
        """Test that all features have required metadata"""
        manager = FeatureUnlockManager()

        for feature_id, feature_data in manager.feature_definitions.items():
            assert "level" in feature_data
            assert "name" in feature_data
            assert "description" in feature_data
            assert "category" in feature_data
            assert 1 <= feature_data["level"] <= 10

    def test_is_feature_unlocked_level_1(self, test_personality_level_1):
        """Test feature unlock checks at level 1"""
        manager = FeatureUnlockManager()

        # Level 1 features should be unlocked
        assert manager.is_feature_unlocked("basic_chat", 1)
        assert manager.is_feature_unlocked("view_personality", 1)

        # Higher level features should be locked
        assert not manager.is_feature_unlocked("catchphrase_unlocked", 1)
        assert not manager.is_feature_unlocked("advice_mode_unlocked", 1)
        assert not manager.is_feature_unlocked("max_personalization", 1)

    def test_is_feature_unlocked_level_5(self):
        """Test feature unlock checks at level 5"""
        manager = FeatureUnlockManager()

        # Levels 1-5 should be unlocked
        assert manager.is_feature_unlocked("basic_chat", 5)
        assert manager.is_feature_unlocked("profile_unlocked", 5)
        assert manager.is_feature_unlocked("catchphrase_unlocked", 5)
        assert manager.is_feature_unlocked("advice_mode_unlocked", 5)

        # Level 6+ should be locked
        assert not manager.is_feature_unlocked("proactive_help", 5)
        assert not manager.is_feature_unlocked("max_personalization", 5)

    def test_is_feature_unlocked_level_10(self):
        """Test that level 10 unlocks everything"""
        manager = FeatureUnlockManager()

        # All features should be unlocked at level 10
        for feature_id in manager.feature_definitions:
            assert manager.is_feature_unlocked(feature_id, 10)

    def test_get_unlocked_features(self):
        """Test getting list of unlocked features"""
        manager = FeatureUnlockManager()

        # Level 1
        level_1_features = manager.get_unlocked_features(1)
        assert len(level_1_features) > 0
        assert all(f["level"] == 1 for f in level_1_features)

        # Level 5
        level_5_features = manager.get_unlocked_features(5)
        assert len(level_5_features) > len(level_1_features)
        assert all(f["level"] <= 5 for f in level_5_features)

        # Level 10
        level_10_features = manager.get_unlocked_features(10)
        assert len(level_10_features) == len(manager.feature_definitions)

    def test_get_locked_features(self):
        """Test getting list of locked features"""
        manager = FeatureUnlockManager()

        # Level 1 - most features locked
        level_1_locked = manager.get_locked_features(1)
        assert len(level_1_locked) > 0

        # Level 5 - some features locked
        level_5_locked = manager.get_locked_features(5)
        assert len(level_5_locked) < len(level_1_locked)
        assert all(f["level"] > 5 for f in level_5_locked)

        # Level 10 - no features locked
        level_10_locked = manager.get_locked_features(10)
        assert len(level_10_locked) == 0

    def test_get_features_by_level(self):
        """Test getting features that unlock at specific level"""
        manager = FeatureUnlockManager()

        # Level 1
        level_1 = manager.get_features_by_level(1)
        assert len(level_1) > 0
        assert all(f["level"] == 1 for f in level_1)

        # Level 3
        level_3 = manager.get_features_by_level(3)
        assert len(level_3) > 0
        assert all(f["level"] == 3 for f in level_3)
        # Should include catchphrase_unlocked
        assert any(f["id"] == "catchphrase_unlocked" for f in level_3)

    def test_get_features_by_category(self):
        """Test getting features by category"""
        manager = FeatureUnlockManager()

        # Conversation features
        conv_features = manager.get_features_by_category("conversation")
        assert len(conv_features) > 0
        assert all(f["category"] == "conversation" for f in conv_features)

        # Memory features
        memory_features = manager.get_features_by_category("memory")
        assert len(memory_features) > 0
        assert all(f["category"] == "memory" for f in memory_features)

    def test_get_features_by_category_filtered(self):
        """Test getting features by category filtered by level"""
        manager = FeatureUnlockManager()

        # All conversation features
        all_conv = manager.get_features_by_category("conversation")

        # Conversation features unlocked at level 3
        level_3_conv = manager.get_features_by_category("conversation", 3)

        assert len(level_3_conv) <= len(all_conv)
        assert all(f["level"] <= 3 for f in level_3_conv)

    def test_get_feature_info(self):
        """Test getting feature information"""
        manager = FeatureUnlockManager()

        info = manager.get_feature_info("catchphrase_unlocked")
        assert info is not None
        assert info["id"] == "catchphrase_unlocked"
        assert info["level"] == 3
        assert info["name"]
        assert info["description"]
        assert info["category"]

    def test_get_feature_info_nonexistent(self):
        """Test getting info for nonexistent feature"""
        manager = FeatureUnlockManager()

        info = manager.get_feature_info("nonexistent_feature")
        assert info is None

    def test_get_feature_summary(self, test_personality_level_5):
        """Test getting comprehensive feature summary"""
        manager = FeatureUnlockManager()

        summary = manager.get_feature_summary(test_personality_level_5)

        assert summary["current_level"] == 5
        assert summary["total_features"] == len(manager.feature_definitions)
        assert summary["unlocked_count"] > 0
        assert summary["locked_count"] > 0
        assert summary["unlocked_count"] + summary["locked_count"] == summary["total_features"]
        assert "unlocked_features" in summary
        assert "locked_features" in summary
        assert "by_category" in summary
        assert "next_level_features" in summary
        assert "unlock_percentage" in summary

    def test_check_multiple_features(self):
        """Test checking multiple features at once"""
        manager = FeatureUnlockManager()

        features_to_check = [
            "basic_chat",
            "catchphrase_unlocked",
            "advice_mode_unlocked",
            "max_personalization",
        ]

        results = manager.check_multiple_features(features_to_check, 5)

        assert results["basic_chat"] is True  # Level 1
        assert results["catchphrase_unlocked"] is True  # Level 3
        assert results["advice_mode_unlocked"] is True  # Level 5
        assert results["max_personalization"] is False  # Level 10


class TestFeatureGates:
    """Test feature gating functionality"""

    def test_check_feature_access_unlocked(self, test_personality_level_5):
        """Test checking access to unlocked feature"""
        assert check_feature_access(test_personality_level_5, "basic_chat")
        assert check_feature_access(test_personality_level_5, "advice_mode_unlocked")

    def test_check_feature_access_locked(self, test_personality_level_5):
        """Test checking access to locked feature"""
        assert not check_feature_access(test_personality_level_5, "proactive_help")
        assert not check_feature_access(test_personality_level_5, "max_personalization")

    def test_check_feature_access_with_exception(self, test_personality_level_5):
        """Test checking feature access with exception raising"""
        # Should not raise for unlocked
        check_feature_access(test_personality_level_5, "basic_chat", raise_exception=True)

        # Should raise for locked
        with pytest.raises(FeatureNotUnlockedException) as exc_info:
            check_feature_access(
                test_personality_level_5, "proactive_help", raise_exception=True
            )

        assert exc_info.value.feature_id == "proactive_help"
        assert exc_info.value.required_level == 6
        assert exc_info.value.current_level == 5

    def test_get_feature_gate_message(self, test_personality_level_5):
        """Test getting feature lock message"""
        message = get_feature_gate_message("proactive_help", test_personality_level_5)

        assert "locked" in message.lower() or "🔒" in message
        assert "Proactive" in message  # Feature name
        assert "level 6" in message.lower() or "Level 6" in message

    def test_can_use_catchphrase(self, test_personality_level_1, test_personality_level_5):
        """Test catchphrase feature check"""
        # Level 1 - locked
        assert not can_use_catchphrase(test_personality_level_1)

        # Level 5 - unlocked
        assert can_use_catchphrase(test_personality_level_5)

    def test_can_give_advice(self, test_personality_level_1, test_personality_level_5):
        """Test advice mode feature check"""
        # Level 1 - locked
        assert not can_give_advice(test_personality_level_1)

        # Level 5 - unlocked
        assert can_give_advice(test_personality_level_5)

    def test_require_feature_decorator_unlocked(self, test_personality_level_5):
        """Test require_feature decorator with unlocked feature"""

        @require_feature("advice_mode_unlocked")
        def give_advice(personality):
            return "Here's some advice!"

        # Should work fine
        result = give_advice(test_personality_level_5)
        assert result == "Here's some advice!"

    def test_require_feature_decorator_locked(self, test_personality_level_1):
        """Test require_feature decorator with locked feature"""

        @require_feature("advice_mode_unlocked")
        def give_advice(personality):
            return "Here's some advice!"

        # Should raise exception
        with pytest.raises(FeatureNotUnlockedException):
            give_advice(test_personality_level_1)


class TestConvenienceFunctions:
    """Test convenience functions"""

    def test_is_feature_unlocked_function(self):
        """Test is_feature_unlocked convenience function"""
        assert is_feature_unlocked("basic_chat", 1)
        assert is_feature_unlocked("catchphrase_unlocked", 3)
        assert not is_feature_unlocked("catchphrase_unlocked", 2)

    def test_get_unlocked_features_function(self):
        """Test get_unlocked_features convenience function"""
        features = get_unlocked_features(5)
        assert len(features) > 0
        assert all(f["level"] <= 5 for f in features)

    def test_get_feature_summary_function(self, test_personality_level_5):
        """Test get_feature_summary convenience function"""
        summary = get_feature_summary(test_personality_level_5)
        assert summary["current_level"] == 5
        assert "unlocked_features" in summary


class TestFeatureCategories:
    """Test feature categories"""

    def test_all_categories_defined(self):
        """Test that all categories are defined"""
        manager = FeatureUnlockManager()

        assert len(manager.categories) > 0
        assert "conversation" in manager.categories
        assert "personality" in manager.categories
        assert "memory" in manager.categories

    def test_all_features_have_valid_category(self):
        """Test that all features use valid categories"""
        manager = FeatureUnlockManager()

        for feature_data in manager.feature_definitions.values():
            assert feature_data["category"] in manager.categories


class TestProgressiveUnlocking:
    """Test progressive feature unlocking"""

    def test_level_progression(self):
        """Test that features unlock progressively"""
        manager = FeatureUnlockManager()

        for level in range(1, 11):
            unlocked = manager.get_unlocked_features(level)
            unlocked_count = len(unlocked)

            # Each level should unlock same or more features
            if level < 10:
                next_unlocked = manager.get_unlocked_features(level + 1)
                assert len(next_unlocked) >= unlocked_count

    def test_no_duplicate_unlocks(self):
        """Test that each feature only unlocks once"""
        manager = FeatureUnlockManager()

        feature_levels = {}
        for feature_id, feature_data in manager.feature_definitions.items():
            level = feature_data["level"]
            if level not in feature_levels:
                feature_levels[level] = []
            feature_levels[level].append(feature_id)

        # Each feature should appear in exactly one level
        all_features = []
        for features in feature_levels.values():
            all_features.extend(features)

        assert len(all_features) == len(set(all_features))  # No duplicates


class TestEdgeCases:
    """Test edge cases"""

    def test_invalid_feature_id(self):
        """Test checking invalid feature ID"""
        manager = FeatureUnlockManager()

        assert not manager.is_feature_unlocked("invalid_feature", 5)

    def test_level_out_of_range(self):
        """Test with levels outside 1-10 range"""
        manager = FeatureUnlockManager()

        # Level 0
        unlocked = manager.get_unlocked_features(0)
        assert len(unlocked) == 0

        # Level 11+
        unlocked = manager.get_unlocked_features(11)
        # Should return all features
        assert len(unlocked) == len(manager.feature_definitions)

    def test_empty_feature_check(self):
        """Test checking empty list of features"""
        manager = FeatureUnlockManager()

        results = manager.check_multiple_features([], 5)
        assert results == {}
