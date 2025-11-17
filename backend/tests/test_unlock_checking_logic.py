"""
Tests for Unlock Checking Logic
Comprehensive tests for feature unlock checking mechanisms
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.personality import BotPersonality
from models.user import User
from models.level_up_event import LevelUpEvent  # Import to resolve SQLAlchemy relationship
from database.database import Base
from services.feature_unlock_manager import (
    FeatureUnlockManager,
    feature_unlock_manager,
    is_feature_unlocked,
    get_unlocked_features,
)
from services.feature_gates import (
    FeatureNotUnlockedException,
    require_feature,
    check_feature_access,
    get_feature_gate_message,
    apply_feature_modifiers,
    get_conversation_features,
    get_memory_features,
    get_personality_features,
    can_use_catchphrase,
    can_give_advice,
    can_share_interests,
    can_celebrate_milestones,
    can_create_inside_jokes,
    has_max_personalization,
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
    user = User(id=1, name="Test User", age=12, grade=6)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def create_personality_at_level(db_session, user_id, level):
    """Helper to create personality at specific level"""
    personality = BotPersonality(
        user_id=user_id,
        name="TestBot",
        friendship_level=level,
        friendship_points=level * 100,
        humor=0.5,
        energy=0.5,
        curiosity=0.5,
        formality=0.3,
    )
    db_session.add(personality)
    db_session.commit()
    db_session.refresh(personality)
    return personality


class TestCoreUnlockChecking:
    """Test core unlock checking logic"""

    def test_is_feature_unlocked_exact_level(self):
        """Test feature unlocked at exact required level"""
        manager = FeatureUnlockManager()

        # Catchphrase unlocks at level 3
        assert manager.is_feature_unlocked("catchphrase_unlocked", 3)

    def test_is_feature_unlocked_higher_level(self):
        """Test feature unlocked at higher level"""
        manager = FeatureUnlockManager()

        # Catchphrase unlocks at level 3, should be available at 5
        assert manager.is_feature_unlocked("catchphrase_unlocked", 5)
        assert manager.is_feature_unlocked("catchphrase_unlocked", 10)

    def test_is_feature_locked_lower_level(self):
        """Test feature locked at lower level"""
        manager = FeatureUnlockManager()

        # Catchphrase unlocks at level 3
        assert not manager.is_feature_unlocked("catchphrase_unlocked", 1)
        assert not manager.is_feature_unlocked("catchphrase_unlocked", 2)

    def test_is_feature_unlocked_level_1_features(self):
        """Test that level 1 features are always unlocked"""
        manager = FeatureUnlockManager()

        # These should be unlocked at all levels
        for level in range(1, 11):
            assert manager.is_feature_unlocked("basic_chat", level)
            assert manager.is_feature_unlocked("view_personality", level)

    def test_is_feature_unlocked_level_10_unlocks_all(self):
        """Test that level 10 unlocks everything"""
        manager = FeatureUnlockManager()

        # All features should be unlocked at level 10
        for feature_id in manager.feature_definitions:
            assert manager.is_feature_unlocked(feature_id, 10)

    def test_is_feature_unlocked_unknown_feature(self):
        """Test checking unknown feature returns False"""
        manager = FeatureUnlockManager()

        assert not manager.is_feature_unlocked("nonexistent_feature", 5)

    def test_is_feature_unlocked_all_levels(self):
        """Test specific features at all levels"""
        manager = FeatureUnlockManager()

        test_cases = [
            ("basic_chat", 1),
            ("profile_unlocked", 2),
            ("catchphrase_unlocked", 3),
            ("interests_shared", 4),
            ("advice_mode_unlocked", 5),
            ("proactive_help", 6),
            ("custom_activities", 7),
            ("inside_jokes", 8),
            ("life_advice", 9),
            ("max_personalization", 10),
        ]

        for feature_id, required_level in test_cases:
            # Should be locked below required level
            for level in range(1, required_level):
                assert not manager.is_feature_unlocked(feature_id, level), \
                    f"{feature_id} should be locked at level {level}"

            # Should be unlocked at and above required level
            for level in range(required_level, 11):
                assert manager.is_feature_unlocked(feature_id, level), \
                    f"{feature_id} should be unlocked at level {level}"


class TestFeatureAccessChecking:
    """Test check_feature_access function"""

    def test_check_access_unlocked_feature(self, db_session, test_user):
        """Test checking access to unlocked feature"""
        personality = create_personality_at_level(db_session, test_user.id, 5)

        # Level 5 has advice mode
        assert check_feature_access(personality, "advice_mode_unlocked")
        assert check_feature_access(personality, "basic_chat")
        assert check_feature_access(personality, "catchphrase_unlocked")

    def test_check_access_locked_feature(self, db_session, test_user):
        """Test checking access to locked feature"""
        personality = create_personality_at_level(db_session, test_user.id, 3)

        # Level 3 doesn't have these
        assert not check_feature_access(personality, "advice_mode_unlocked")
        assert not check_feature_access(personality, "proactive_help")
        assert not check_feature_access(personality, "max_personalization")

    def test_check_access_with_exception_unlocked(self, db_session, test_user):
        """Test that no exception raised for unlocked features"""
        personality = create_personality_at_level(db_session, test_user.id, 5)

        # Should not raise
        result = check_feature_access(
            personality, "advice_mode_unlocked", raise_exception=True
        )
        assert result is True

    def test_check_access_with_exception_locked(self, db_session, test_user):
        """Test that exception raised for locked features"""
        personality = create_personality_at_level(db_session, test_user.id, 3)

        # Should raise exception
        with pytest.raises(FeatureNotUnlockedException) as exc_info:
            check_feature_access(
                personality, "advice_mode_unlocked", raise_exception=True
            )

        assert exc_info.value.feature_id == "advice_mode_unlocked"
        assert exc_info.value.required_level == 5
        assert exc_info.value.current_level == 3

    def test_check_access_boundary_conditions(self, db_session, test_user):
        """Test boundary conditions for feature access"""
        # Test at exact unlock level
        personality_3 = create_personality_at_level(db_session, 10, 3)
        assert check_feature_access(personality_3, "catchphrase_unlocked")

        # Test one level below
        personality_2 = create_personality_at_level(db_session, 11, 2)
        assert not check_feature_access(personality_2, "catchphrase_unlocked")

        # Test one level above
        personality_4 = create_personality_at_level(db_session, 12, 4)
        assert check_feature_access(personality_4, "catchphrase_unlocked")


class TestRequireFeatureDecorator:
    """Test @require_feature decorator"""

    def test_decorator_allows_unlocked_feature(self, db_session, test_user):
        """Test decorator allows function when feature unlocked"""
        personality = create_personality_at_level(db_session, test_user.id, 5)

        @require_feature("advice_mode_unlocked")
        def give_advice(pers):
            return f"Advice from {pers.name}"

        # Should work
        result = give_advice(personality)
        assert result == "Advice from TestBot"

    def test_decorator_blocks_locked_feature(self, db_session, test_user):
        """Test decorator blocks function when feature locked"""
        personality = create_personality_at_level(db_session, test_user.id, 3)

        @require_feature("advice_mode_unlocked")
        def give_advice(pers):
            return "Advice"

        # Should raise exception
        with pytest.raises(FeatureNotUnlockedException) as exc_info:
            give_advice(personality)

        assert exc_info.value.feature_id == "advice_mode_unlocked"
        assert exc_info.value.current_level == 3

    def test_decorator_with_kwargs(self, db_session, test_user):
        """Test decorator works with keyword arguments"""
        personality = create_personality_at_level(db_session, test_user.id, 5)

        @require_feature("advice_mode_unlocked")
        def give_advice(personality, topic):
            return f"Advice about {topic}"

        # Should work with kwargs
        result = give_advice(personality=personality, topic="friendship")
        assert result == "Advice about friendship"

    def test_decorator_without_personality_allows(self):
        """Test decorator allows when personality not found"""

        @require_feature("advice_mode_unlocked")
        def some_function(data):
            return data * 2

        # Should allow (can't check without personality)
        result = some_function(5)
        assert result == 10

    def test_decorator_multiple_features(self, db_session, test_user):
        """Test multiple decorators stack correctly"""
        personality = create_personality_at_level(db_session, test_user.id, 5)

        @require_feature("advice_mode_unlocked")
        @require_feature("catchphrase_unlocked")
        def special_function(pers):
            return "special"

        # Both unlocked at level 5
        result = special_function(personality)
        assert result == "special"

    def test_decorator_multiple_features_one_locked(self, db_session, test_user):
        """Test multiple decorators block when one locked"""
        personality = create_personality_at_level(db_session, test_user.id, 3)

        @require_feature("advice_mode_unlocked")  # Level 5 - locked
        @require_feature("catchphrase_unlocked")  # Level 3 - unlocked
        def special_function(pers):
            return "special"

        # Should raise because advice_mode is locked
        with pytest.raises(FeatureNotUnlockedException):
            special_function(personality)


class TestFeatureGateMessages:
    """Test feature gate message generation"""

    def test_gate_message_structure(self, db_session, test_user):
        """Test gate message contains required elements"""
        personality = create_personality_at_level(db_session, test_user.id, 3)

        message = get_feature_gate_message("advice_mode_unlocked", personality)

        # Should contain feature name
        assert "Advice Mode" in message

        # Should indicate locked status
        assert "🔒" in message or "locked" in message.lower()

        # Should mention level requirement
        assert "5" in message or "Level 5" in message

    def test_gate_message_one_level_away(self, db_session, test_user):
        """Test message when one level away"""
        personality = create_personality_at_level(db_session, test_user.id, 4)

        message = get_feature_gate_message("advice_mode_unlocked", personality)

        # Should mention being close
        assert "Level 5" in message

    def test_gate_message_many_levels_away(self, db_session, test_user):
        """Test message when many levels away"""
        personality = create_personality_at_level(db_session, test_user.id, 2)

        message = get_feature_gate_message("max_personalization", personality)

        # Should mention how many levels needed
        assert "Level 10" in message

    def test_gate_message_invalid_feature(self, db_session, test_user):
        """Test message for invalid feature"""
        personality = create_personality_at_level(db_session, test_user.id, 5)

        message = get_feature_gate_message("nonexistent_feature", personality)

        # Should have generic message
        assert "not available" in message.lower()

    def test_gate_message_includes_description(self, db_session, test_user):
        """Test message includes feature description"""
        personality = create_personality_at_level(db_session, test_user.id, 3)

        message = get_feature_gate_message("advice_mode_unlocked", personality)

        # Should contain description from feature definition
        assert "guidance" in message.lower() or "advice" in message.lower()


class TestFeatureModifiers:
    """Test apply_feature_modifiers function"""

    def test_modifiers_deeper_conversations(self, db_session, test_user):
        """Test deeper conversations modifier"""
        personality = create_personality_at_level(db_session, test_user.id, 4)

        base_config = {"max_context_messages": 5, "max_memory_items": 5}
        modified = apply_feature_modifiers(personality, base_config)

        # Should increase context and memory
        assert modified["max_context_messages"] > base_config["max_context_messages"]
        assert modified["max_memory_items"] > base_config["max_memory_items"]

    def test_modifiers_emotional_support(self, db_session, test_user):
        """Test emotional support modifier"""
        personality = create_personality_at_level(db_session, test_user.id, 5)

        base_config = {}
        modified = apply_feature_modifiers(personality, base_config)

        # Should enable empathy and mood detection
        assert modified.get("empathy_mode") is True
        assert modified.get("mood_detection_enabled") is True

    def test_modifiers_proactive_help(self, db_session, test_user):
        """Test proactive help modifier"""
        personality = create_personality_at_level(db_session, test_user.id, 6)

        base_config = {}
        modified = apply_feature_modifiers(personality, base_config)

        # Should enable suggestions
        assert modified.get("proactive_suggestions") is True
        assert "suggestion_frequency" in modified

    def test_modifiers_max_personalization(self, db_session, test_user):
        """Test max personalization modifier"""
        personality = create_personality_at_level(db_session, test_user.id, 10)

        base_config = {}
        modified = apply_feature_modifiers(personality, base_config)

        # Should enable maximum personalization
        assert modified.get("personalization_level") == "maximum"
        assert modified.get("all_customization_enabled") is True

    def test_modifiers_dont_modify_original(self, db_session, test_user):
        """Test that modifiers don't change original config"""
        personality = create_personality_at_level(db_session, test_user.id, 10)

        base_config = {"setting": "value"}
        modified = apply_feature_modifiers(personality, base_config)

        # Original should be unchanged
        assert base_config == {"setting": "value"}
        # Modified should have additions
        assert "personalization_level" in modified

    def test_modifiers_cumulative(self, db_session, test_user):
        """Test that modifiers accumulate at higher levels"""
        personality = create_personality_at_level(db_session, test_user.id, 10)

        base_config = {}
        modified = apply_feature_modifiers(personality, base_config)

        # Should have modifiers from multiple levels
        assert "empathy_mode" in modified  # Level 5
        assert "proactive_suggestions" in modified  # Level 6
        assert "personalization_level" in modified  # Level 10


class TestConversationFeatures:
    """Test get_conversation_features function"""

    def test_conversation_features_level_1(self, db_session, test_user):
        """Test conversation features at level 1"""
        personality = create_personality_at_level(db_session, test_user.id, 1)

        features = get_conversation_features(personality)

        assert features["basic_chat"] is True
        assert features["advice_mode"] is False
        assert features["proactive_help"] is False

    def test_conversation_features_level_5(self, db_session, test_user):
        """Test conversation features at level 5"""
        personality = create_personality_at_level(db_session, test_user.id, 5)

        features = get_conversation_features(personality)

        assert features["basic_chat"] is True
        assert features["casual_mode"] is True
        assert features["deeper_conversations"] is True
        assert features["advice_mode"] is True
        assert features["emotional_support"] is True
        assert features["proactive_help"] is False  # Level 6

    def test_conversation_features_level_10(self, db_session, test_user):
        """Test all conversation features at level 10"""
        personality = create_personality_at_level(db_session, test_user.id, 10)

        features = get_conversation_features(personality)

        # All should be unlocked
        for feature, unlocked in features.items():
            assert unlocked is True, f"{feature} should be unlocked at level 10"


class TestMemoryFeatures:
    """Test get_memory_features function"""

    def test_memory_features_level_1(self, db_session, test_user):
        """Test memory features at level 1"""
        personality = create_personality_at_level(db_session, test_user.id, 1)

        features = get_memory_features(personality)

        assert features["save_memories"] is False  # Level 2
        assert features["favorites"] is False  # Level 3
        assert features["legacy_archive"] is False  # Level 10

    def test_memory_features_level_5(self, db_session, test_user):
        """Test memory features at level 5"""
        personality = create_personality_at_level(db_session, test_user.id, 5)

        features = get_memory_features(personality)

        assert features["save_memories"] is True
        assert features["favorites"] is True
        assert features["goals"] is True
        assert features["achievements"] is True
        assert features["legacy_archive"] is False  # Level 10

    def test_memory_features_level_10(self, db_session, test_user):
        """Test all memory features at level 10"""
        personality = create_personality_at_level(db_session, test_user.id, 10)

        features = get_memory_features(personality)

        # All should be unlocked
        for feature, unlocked in features.items():
            assert unlocked is True, f"{feature} should be unlocked at level 10"


class TestPersonalityFeatures:
    """Test get_personality_features function"""

    def test_personality_features_level_1(self, db_session, test_user):
        """Test personality features at level 1"""
        personality = create_personality_at_level(db_session, test_user.id, 1)

        features = get_personality_features(personality)

        assert features["catchphrase"] is False  # Level 3
        assert features["shared_interests"] is False  # Level 4
        assert features["max_personalization"] is False  # Level 10

    def test_personality_features_progressive_unlock(self, db_session):
        """Test personality features unlock progressively"""
        # Level 3 - catchphrase
        pers_3 = create_personality_at_level(db_session, 20, 3)
        features_3 = get_personality_features(pers_3)
        assert features_3["catchphrase"] is True
        assert features_3["shared_interests"] is False

        # Level 4 - shared interests
        pers_4 = create_personality_at_level(db_session, 21, 4)
        features_4 = get_personality_features(pers_4)
        assert features_4["catchphrase"] is True
        assert features_4["shared_interests"] is True
        assert features_4["inside_jokes"] is False

        # Level 8 - inside jokes
        pers_8 = create_personality_at_level(db_session, 22, 8)
        features_8 = get_personality_features(pers_8)
        assert features_8["inside_jokes"] is True
        assert features_8["max_personalization"] is False

        # Level 10 - max personalization
        pers_10 = create_personality_at_level(db_session, 23, 10)
        features_10 = get_personality_features(pers_10)
        assert features_10["max_personalization"] is True


class TestHelperFunctions:
    """Test feature-specific helper functions"""

    def test_can_use_catchphrase(self, db_session):
        """Test can_use_catchphrase helper"""
        pers_2 = create_personality_at_level(db_session, 30, 2)
        assert can_use_catchphrase(pers_2) is False

        pers_3 = create_personality_at_level(db_session, 31, 3)
        assert can_use_catchphrase(pers_3) is True

        pers_5 = create_personality_at_level(db_session, 32, 5)
        assert can_use_catchphrase(pers_5) is True

    def test_can_give_advice(self, db_session):
        """Test can_give_advice helper"""
        pers_4 = create_personality_at_level(db_session, 40, 4)
        assert can_give_advice(pers_4) is False

        pers_5 = create_personality_at_level(db_session, 41, 5)
        assert can_give_advice(pers_5) is True

        pers_10 = create_personality_at_level(db_session, 42, 10)
        assert can_give_advice(pers_10) is True

    def test_can_share_interests(self, db_session):
        """Test can_share_interests helper"""
        pers_3 = create_personality_at_level(db_session, 50, 3)
        assert can_share_interests(pers_3) is False

        pers_4 = create_personality_at_level(db_session, 51, 4)
        assert can_share_interests(pers_4) is True

    def test_can_celebrate_milestones(self, db_session):
        """Test can_celebrate_milestones helper"""
        pers_5 = create_personality_at_level(db_session, 60, 5)
        assert can_celebrate_milestones(pers_5) is False

        pers_6 = create_personality_at_level(db_session, 61, 6)
        assert can_celebrate_milestones(pers_6) is True

    def test_can_create_inside_jokes(self, db_session):
        """Test can_create_inside_jokes helper"""
        pers_7 = create_personality_at_level(db_session, 70, 7)
        assert can_create_inside_jokes(pers_7) is False

        pers_8 = create_personality_at_level(db_session, 71, 8)
        assert can_create_inside_jokes(pers_8) is True

    def test_has_max_personalization(self, db_session):
        """Test has_max_personalization helper"""
        pers_9 = create_personality_at_level(db_session, 80, 9)
        assert has_max_personalization(pers_9) is False

        pers_10 = create_personality_at_level(db_session, 81, 10)
        assert has_max_personalization(pers_10) is True


class TestUnlockCheckingEdgeCases:
    """Test edge cases for unlock checking"""

    def test_level_zero(self):
        """Test behavior with level 0"""
        manager = FeatureUnlockManager()

        # Nothing should be unlocked at level 0
        assert not manager.is_feature_unlocked("basic_chat", 0)

    def test_negative_level(self):
        """Test behavior with negative level"""
        manager = FeatureUnlockManager()

        # Nothing should be unlocked at negative level
        assert not manager.is_feature_unlocked("basic_chat", -1)

    def test_level_above_max(self):
        """Test behavior with level above 10"""
        manager = FeatureUnlockManager()

        # Everything should be unlocked
        for feature_id in manager.feature_definitions:
            assert manager.is_feature_unlocked(feature_id, 11)
            assert manager.is_feature_unlocked(feature_id, 100)

    def test_empty_feature_id(self):
        """Test checking empty feature ID"""
        manager = FeatureUnlockManager()

        assert not manager.is_feature_unlocked("", 5)

    def test_none_feature_id(self):
        """Test checking None as feature ID"""
        manager = FeatureUnlockManager()

        # Should handle gracefully
        result = manager.is_feature_unlocked(None, 5)
        assert result is False

    def test_case_sensitivity(self):
        """Test that feature IDs are case sensitive"""
        manager = FeatureUnlockManager()

        # Correct case
        assert manager.is_feature_unlocked("basic_chat", 1)

        # Wrong case - should not match
        assert not manager.is_feature_unlocked("Basic_Chat", 1)
        assert not manager.is_feature_unlocked("BASIC_CHAT", 1)


class TestConvenienceFunctions:
    """Test convenience wrapper functions"""

    def test_is_feature_unlocked_convenience(self):
        """Test is_feature_unlocked convenience function"""
        assert is_feature_unlocked("basic_chat", 1)
        assert is_feature_unlocked("catchphrase_unlocked", 3)
        assert not is_feature_unlocked("catchphrase_unlocked", 2)
        assert is_feature_unlocked("max_personalization", 10)

    def test_get_unlocked_features_convenience(self):
        """Test get_unlocked_features convenience function"""
        features_1 = get_unlocked_features(1)
        assert len(features_1) > 0
        assert all(f["level"] == 1 for f in features_1)

        features_5 = get_unlocked_features(5)
        assert len(features_5) > len(features_1)
        assert all(f["level"] <= 5 for f in features_5)

    def test_convenience_functions_match_manager(self):
        """Test that convenience functions match manager behavior"""
        manager = FeatureUnlockManager()

        # is_feature_unlocked
        assert (
            is_feature_unlocked("advice_mode_unlocked", 5)
            == manager.is_feature_unlocked("advice_mode_unlocked", 5)
        )

        # get_unlocked_features
        conv_result = get_unlocked_features(5)
        manager_result = manager.get_unlocked_features(5)

        assert len(conv_result) == len(manager_result)


class TestCheckMultipleFeatures:
    """Test batch checking of multiple features"""

    def test_check_multiple_all_unlocked(self):
        """Test checking multiple unlocked features"""
        manager = FeatureUnlockManager()

        features = ["basic_chat", "catchphrase_unlocked", "advice_mode_unlocked"]
        results = manager.check_multiple_features(features, 5)

        assert results["basic_chat"] is True
        assert results["catchphrase_unlocked"] is True
        assert results["advice_mode_unlocked"] is True

    def test_check_multiple_mixed(self):
        """Test checking mix of locked and unlocked"""
        manager = FeatureUnlockManager()

        features = [
            "basic_chat",  # Level 1 - unlocked
            "catchphrase_unlocked",  # Level 3 - unlocked
            "advice_mode_unlocked",  # Level 5 - locked
            "max_personalization",  # Level 10 - locked
        ]
        results = manager.check_multiple_features(features, 3)

        assert results["basic_chat"] is True
        assert results["catchphrase_unlocked"] is True
        assert results["advice_mode_unlocked"] is False
        assert results["max_personalization"] is False

    def test_check_multiple_empty_list(self):
        """Test checking empty feature list"""
        manager = FeatureUnlockManager()

        results = manager.check_multiple_features([], 5)
        assert results == {}

    def test_check_multiple_with_invalid(self):
        """Test checking includes invalid feature"""
        manager = FeatureUnlockManager()

        features = ["basic_chat", "invalid_feature", "catchphrase_unlocked"]
        results = manager.check_multiple_features(features, 5)

        assert results["basic_chat"] is True
        assert results["invalid_feature"] is False
        assert results["catchphrase_unlocked"] is True


class TestUnlockConsistency:
    """Test consistency of unlock checking across methods"""

    def test_consistency_across_methods(self, db_session, test_user):
        """Test that different methods give consistent results"""
        personality = create_personality_at_level(db_session, test_user.id, 5)
        manager = FeatureUnlockManager()

        # Check via is_feature_unlocked
        unlocked_via_check = manager.is_feature_unlocked(
            "advice_mode_unlocked", personality.friendship_level
        )

        # Check via check_feature_access
        unlocked_via_access = check_feature_access(personality, "advice_mode_unlocked")

        # Check via can_give_advice
        unlocked_via_helper = can_give_advice(personality)

        # All should match
        assert unlocked_via_check == unlocked_via_access == unlocked_via_helper
        assert unlocked_via_check is True

    def test_consistency_locked_feature(self, db_session, test_user):
        """Test consistency for locked features"""
        personality = create_personality_at_level(db_session, test_user.id, 3)
        manager = FeatureUnlockManager()

        # Check via is_feature_unlocked
        locked_via_check = not manager.is_feature_unlocked(
            "advice_mode_unlocked", personality.friendship_level
        )

        # Check via check_feature_access
        locked_via_access = not check_feature_access(
            personality, "advice_mode_unlocked"
        )

        # Check via can_give_advice
        locked_via_helper = not can_give_advice(personality)

        # All should match (all locked)
        assert locked_via_check == locked_via_access == locked_via_helper
        assert locked_via_check is True

    def test_get_unlocked_matches_individual_checks(self):
        """Test that get_unlocked_features matches individual checks"""
        manager = FeatureUnlockManager()

        unlocked_features = manager.get_unlocked_features(5)
        unlocked_ids = {f["id"] for f in unlocked_features}

        # Check each feature individually
        for feature_id in manager.feature_definitions:
            individual_check = manager.is_feature_unlocked(feature_id, 5)

            if individual_check:
                assert feature_id in unlocked_ids
            else:
                assert feature_id not in unlocked_ids
