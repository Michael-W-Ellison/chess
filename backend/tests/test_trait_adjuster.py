"""
Tests for Trait Adjustment System
Tests bounded trait adjustments with validation
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.database import Base
from models.user import User
from models.personality import BotPersonality
from services.trait_adjuster import TraitAdjuster, trait_adjuster


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
        energy=0.6,
        curiosity=0.5,
        formality=0.3,
        friendship_level=1,
        mood="happy",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    test_db.add(personality)
    test_db.commit()
    test_db.refresh(personality)
    return personality


class TestTraitAdjusterInitialization:
    """Test trait adjuster initialization"""

    def test_adjuster_constants(self):
        """Test adjuster has correct constants"""
        adjuster = TraitAdjuster()

        assert adjuster.TRAIT_MIN == 0.0
        assert adjuster.TRAIT_MAX == 1.0
        assert "humor" in adjuster.VALID_TRAITS
        assert "energy" in adjuster.VALID_TRAITS
        assert "curiosity" in adjuster.VALID_TRAITS
        assert "formality" in adjuster.VALID_TRAITS
        assert len(adjuster.VALID_TRAITS) == 4

    def test_default_values(self):
        """Test default trait values are defined"""
        adjuster = TraitAdjuster()

        assert adjuster.DEFAULT_TRAIT_VALUES["humor"] == 0.5
        assert adjuster.DEFAULT_TRAIT_VALUES["energy"] == 0.6
        assert adjuster.DEFAULT_TRAIT_VALUES["curiosity"] == 0.5
        assert adjuster.DEFAULT_TRAIT_VALUES["formality"] == 0.3


class TestTraitValidation:
    """Test trait name and value validation"""

    def test_validate_trait_name_valid(self):
        """Test validation accepts valid trait names"""
        adjuster = TraitAdjuster()

        assert adjuster.validate_trait_name("humor") is True
        assert adjuster.validate_trait_name("energy") is True
        assert adjuster.validate_trait_name("curiosity") is True
        assert adjuster.validate_trait_name("formality") is True

    def test_validate_trait_name_invalid(self):
        """Test validation rejects invalid trait names"""
        adjuster = TraitAdjuster()

        assert adjuster.validate_trait_name("invalid") is False
        assert adjuster.validate_trait_name("strength") is False
        assert adjuster.validate_trait_name("") is False
        assert adjuster.validate_trait_name("Humor") is False  # Case sensitive

    def test_validate_trait_value_valid(self):
        """Test validation accepts valid trait values"""
        adjuster = TraitAdjuster()

        assert adjuster.validate_trait_value(0.0) is True
        assert adjuster.validate_trait_value(0.5) is True
        assert adjuster.validate_trait_value(1.0) is True
        assert adjuster.validate_trait_value(0.25) is True
        assert adjuster.validate_trait_value(0.75) is True

    def test_validate_trait_value_invalid(self):
        """Test validation rejects invalid trait values"""
        adjuster = TraitAdjuster()

        assert adjuster.validate_trait_value(-0.1) is False
        assert adjuster.validate_trait_value(1.1) is False
        assert adjuster.validate_trait_value(-1.0) is False
        assert adjuster.validate_trait_value(2.0) is False


class TestValueClamping:
    """Test value clamping to bounds"""

    def test_clamp_value_within_bounds(self):
        """Test clamping doesn't change values within bounds"""
        adjuster = TraitAdjuster()

        assert adjuster.clamp_value(0.5) == 0.5
        assert adjuster.clamp_value(0.0) == 0.0
        assert adjuster.clamp_value(1.0) == 1.0
        assert adjuster.clamp_value(0.25) == 0.25

    def test_clamp_value_above_max(self):
        """Test clamping values above maximum"""
        adjuster = TraitAdjuster()

        assert adjuster.clamp_value(1.5) == 1.0
        assert adjuster.clamp_value(2.0) == 1.0
        assert adjuster.clamp_value(100.0) == 1.0

    def test_clamp_value_below_min(self):
        """Test clamping values below minimum"""
        adjuster = TraitAdjuster()

        assert adjuster.clamp_value(-0.5) == 0.0
        assert adjuster.clamp_value(-1.0) == 0.0
        assert adjuster.clamp_value(-100.0) == 0.0


class TestAdjustTrait:
    """Test adjusting a single trait"""

    def test_adjust_trait_valid(self, test_db, test_personality):
        """Test adjusting a trait to a valid value"""
        adjuster = TraitAdjuster()

        old_val, new_val, change = adjuster.adjust_trait(
            test_personality, "humor", 0.8, test_db
        )

        assert old_val == 0.5
        assert new_val == 0.8
        assert change == 0.3
        assert test_personality.humor == 0.8

    def test_adjust_trait_clamped_high(self, test_db, test_personality):
        """Test adjusting a trait above maximum gets clamped"""
        adjuster = TraitAdjuster()

        old_val, new_val, change = adjuster.adjust_trait(
            test_personality, "humor", 1.5, test_db
        )

        assert old_val == 0.5
        assert new_val == 1.0  # Clamped to max
        assert change == 0.5
        assert test_personality.humor == 1.0

    def test_adjust_trait_clamped_low(self, test_db, test_personality):
        """Test adjusting a trait below minimum gets clamped"""
        adjuster = TraitAdjuster()

        old_val, new_val, change = adjuster.adjust_trait(
            test_personality, "formality", -0.5, test_db
        )

        assert old_val == 0.3
        assert new_val == 0.0  # Clamped to min
        assert change == -0.3
        assert test_personality.formality == 0.0

    def test_adjust_trait_invalid_name(self, test_db, test_personality):
        """Test adjusting an invalid trait name raises error"""
        adjuster = TraitAdjuster()

        with pytest.raises(ValueError, match="Invalid trait name"):
            adjuster.adjust_trait(test_personality, "invalid", 0.5, test_db)

    def test_adjust_trait_no_commit(self, test_db, test_personality):
        """Test adjusting without commit"""
        adjuster = TraitAdjuster()

        old_val, new_val, change = adjuster.adjust_trait(
            test_personality, "humor", 0.8, test_db, commit=False
        )

        assert test_personality.humor == 0.8
        # Value is changed in memory but not committed


class TestAdjustTraitByDelta:
    """Test adjusting a trait by a delta amount"""

    def test_adjust_by_positive_delta(self, test_db, test_personality):
        """Test adjusting by positive delta"""
        adjuster = TraitAdjuster()

        old_val, new_val, change = adjuster.adjust_trait_by_delta(
            test_personality, "humor", 0.2, test_db
        )

        assert old_val == 0.5
        assert new_val == 0.7
        assert change == 0.2
        assert test_personality.humor == 0.7

    def test_adjust_by_negative_delta(self, test_db, test_personality):
        """Test adjusting by negative delta"""
        adjuster = TraitAdjuster()

        old_val, new_val, change = adjuster.adjust_trait_by_delta(
            test_personality, "energy", -0.3, test_db
        )

        assert old_val == 0.6
        assert new_val == 0.3
        assert change == -0.3
        assert test_personality.energy == 0.3

    def test_adjust_by_delta_clamped_high(self, test_db, test_personality):
        """Test delta adjustment gets clamped at maximum"""
        adjuster = TraitAdjuster()

        # humor is 0.5, adding 0.8 would be 1.3, should clamp to 1.0
        old_val, new_val, change = adjuster.adjust_trait_by_delta(
            test_personality, "humor", 0.8, test_db
        )

        assert old_val == 0.5
        assert new_val == 1.0
        assert change == 0.5  # Actual change is less than delta
        assert test_personality.humor == 1.0

    def test_adjust_by_delta_clamped_low(self, test_db, test_personality):
        """Test delta adjustment gets clamped at minimum"""
        adjuster = TraitAdjuster()

        # energy is 0.6, subtracting 1.0 would be -0.4, should clamp to 0.0
        old_val, new_val, change = adjuster.adjust_trait_by_delta(
            test_personality, "energy", -1.0, test_db
        )

        assert old_val == 0.6
        assert new_val == 0.0
        assert change == -0.6  # Actual change is less than delta
        assert test_personality.energy == 0.0


class TestAdjustMultipleTraits:
    """Test adjusting multiple traits at once"""

    def test_adjust_multiple_traits_absolute(self, test_db, test_personality):
        """Test adjusting multiple traits with absolute values"""
        adjuster = TraitAdjuster()

        adjustments = {
            "humor": 0.8,
            "energy": 0.7,
            "curiosity": 0.6,
        }

        results = adjuster.adjust_multiple_traits(
            test_personality, adjustments, test_db, is_delta=False
        )

        assert len(results) == 3
        assert test_personality.humor == 0.8
        assert test_personality.energy == 0.7
        assert test_personality.curiosity == 0.6
        assert test_personality.formality == 0.3  # Unchanged

    def test_adjust_multiple_traits_delta(self, test_db, test_personality):
        """Test adjusting multiple traits with deltas"""
        adjuster = TraitAdjuster()

        adjustments = {
            "humor": 0.1,
            "energy": -0.2,
            "formality": 0.3,
        }

        results = adjuster.adjust_multiple_traits(
            test_personality, adjustments, test_db, is_delta=True
        )

        assert len(results) == 3
        assert test_personality.humor == 0.6  # 0.5 + 0.1
        assert test_personality.energy == 0.4  # 0.6 - 0.2
        assert test_personality.formality == 0.6  # 0.3 + 0.3

    def test_adjust_multiple_traits_with_clamping(self, test_db, test_personality):
        """Test multiple adjustments with some values getting clamped"""
        adjuster = TraitAdjuster()

        adjustments = {
            "humor": 2.0,  # Will be clamped to 1.0
            "energy": -1.0,  # Will be clamped to 0.0
        }

        results = adjuster.adjust_multiple_traits(
            test_personality, adjustments, test_db, is_delta=False
        )

        assert test_personality.humor == 1.0
        assert test_personality.energy == 0.0


class TestResetTrait:
    """Test resetting traits to defaults"""

    def test_reset_single_trait(self, test_db, test_personality):
        """Test resetting a single trait to default"""
        adjuster = TraitAdjuster()

        # Change humor from 0.5 to 0.8
        test_personality.humor = 0.8
        test_db.commit()

        # Reset to default (0.5)
        old_val, new_val, change = adjuster.reset_trait(
            test_personality, "humor", test_db
        )

        assert old_val == 0.8
        assert new_val == 0.5  # Default value
        assert change == -0.3
        assert test_personality.humor == 0.5

    def test_reset_all_traits(self, test_db, test_personality):
        """Test resetting all traits to defaults"""
        adjuster = TraitAdjuster()

        # Change all traits
        test_personality.humor = 0.8
        test_personality.energy = 0.2
        test_personality.curiosity = 0.9
        test_personality.formality = 0.1
        test_db.commit()

        # Reset all to defaults
        results = adjuster.reset_all_traits(test_personality, test_db)

        assert len(results) == 4
        assert test_personality.humor == 0.5  # Default
        assert test_personality.energy == 0.6  # Default
        assert test_personality.curiosity == 0.5  # Default
        assert test_personality.formality == 0.3  # Default


class TestGetTraitValues:
    """Test getting trait values"""

    def test_get_single_trait_value(self, test_personality):
        """Test getting a single trait value"""
        adjuster = TraitAdjuster()

        value = adjuster.get_trait_value(test_personality, "humor")
        assert value == 0.5

    def test_get_single_trait_invalid(self, test_personality):
        """Test getting an invalid trait raises error"""
        adjuster = TraitAdjuster()

        with pytest.raises(ValueError, match="Invalid trait name"):
            adjuster.get_trait_value(test_personality, "invalid")

    def test_get_all_trait_values(self, test_personality):
        """Test getting all trait values"""
        adjuster = TraitAdjuster()

        values = adjuster.get_all_trait_values(test_personality)

        assert len(values) == 4
        assert values["humor"] == 0.5
        assert values["energy"] == 0.6
        assert values["curiosity"] == 0.5
        assert values["formality"] == 0.3


class TestValidateAllTraits:
    """Test validating all traits are within bounds"""

    def test_validate_all_traits_valid(self, test_personality):
        """Test validation passes when all traits are valid"""
        adjuster = TraitAdjuster()

        validation = adjuster.validate_all_traits(test_personality)

        assert len(validation) == 4
        assert all(validation.values())  # All should be True

    def test_validate_all_traits_invalid(self, test_db, test_personality):
        """Test validation fails when trait is out of bounds"""
        adjuster = TraitAdjuster()

        # Manually set invalid value (bypassing adjuster)
        test_personality.humor = 1.5

        validation = adjuster.validate_all_traits(test_personality)

        assert validation["humor"] is False
        assert validation["energy"] is True
        assert validation["curiosity"] is True
        assert validation["formality"] is True


class TestGetTraitInfo:
    """Test getting trait information"""

    def test_get_single_trait_info(self):
        """Test getting information about a single trait"""
        adjuster = TraitAdjuster()

        info = adjuster.get_trait_info("humor")

        assert info["name"] == "Humor"
        assert "description" in info
        assert "high" in info
        assert "low" in info
        assert info["min_value"] == 0.0
        assert info["max_value"] == 1.0
        assert info["default_value"] == 0.5

    def test_get_single_trait_info_invalid(self):
        """Test getting info for invalid trait raises error"""
        adjuster = TraitAdjuster()

        with pytest.raises(ValueError, match="Invalid trait name"):
            adjuster.get_trait_info("invalid")

    def test_get_all_trait_info(self):
        """Test getting information about all traits"""
        adjuster = TraitAdjuster()

        info = adjuster.get_all_trait_info()

        assert len(info) == 4
        assert "humor" in info
        assert "energy" in info
        assert "curiosity" in info
        assert "formality" in info

        # Check each trait has required fields
        for trait_info in info.values():
            assert "name" in trait_info
            assert "description" in trait_info
            assert "min_value" in trait_info
            assert "max_value" in trait_info
            assert "default_value" in trait_info


class TestGlobalInstance:
    """Test global trait_adjuster instance"""

    def test_global_instance_exists(self):
        """Test global instance is accessible"""
        assert trait_adjuster is not None
        assert isinstance(trait_adjuster, TraitAdjuster)

    def test_global_instance_convenience_functions(self, test_db, test_personality):
        """Test convenience functions use global instance"""
        from services.trait_adjuster import (
            adjust_trait,
            adjust_trait_by_delta,
            reset_all_traits,
            get_all_trait_values,
        )

        # Test adjust_trait
        old, new, change = adjust_trait(
            test_personality, "humor", 0.7, test_db
        )
        assert test_personality.humor == 0.7

        # Test adjust_trait_by_delta
        old, new, change = adjust_trait_by_delta(
            test_personality, "energy", 0.1, test_db
        )
        assert test_personality.energy == 0.7

        # Test get_all_trait_values
        values = get_all_trait_values(test_personality)
        assert len(values) == 4

        # Test reset_all_traits
        results = reset_all_traits(test_personality, test_db)
        assert len(results) == 4


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_adjust_to_same_value(self, test_db, test_personality):
        """Test adjusting to the same value"""
        adjuster = TraitAdjuster()

        old_val, new_val, change = adjuster.adjust_trait(
            test_personality, "humor", 0.5, test_db
        )

        assert old_val == 0.5
        assert new_val == 0.5
        assert change == 0.0

    def test_adjust_by_zero_delta(self, test_db, test_personality):
        """Test adjusting by zero delta"""
        adjuster = TraitAdjuster()

        old_val, new_val, change = adjuster.adjust_trait_by_delta(
            test_personality, "humor", 0.0, test_db
        )

        assert old_val == 0.5
        assert new_val == 0.5
        assert change == 0.0

    def test_adjust_to_exact_bounds(self, test_db, test_personality):
        """Test adjusting to exact boundary values"""
        adjuster = TraitAdjuster()

        # Adjust to minimum
        old_val, new_val, change = adjuster.adjust_trait(
            test_personality, "humor", 0.0, test_db
        )
        assert new_val == 0.0

        # Adjust to maximum
        old_val, new_val, change = adjuster.adjust_trait(
            test_personality, "humor", 1.0, test_db
        )
        assert new_val == 1.0

    def test_multiple_sequential_adjustments(self, test_db, test_personality):
        """Test multiple sequential adjustments to same trait"""
        adjuster = TraitAdjuster()

        # Start at 0.5
        assert test_personality.humor == 0.5

        # Adjust to 0.7
        adjuster.adjust_trait(test_personality, "humor", 0.7, test_db)
        assert test_personality.humor == 0.7

        # Adjust to 0.4
        adjuster.adjust_trait(test_personality, "humor", 0.4, test_db)
        assert test_personality.humor == 0.4

        # Adjust to 0.9
        adjuster.adjust_trait(test_personality, "humor", 0.9, test_db)
        assert test_personality.humor == 0.9
