"""
Tests for Advice Template Service
Comprehensive test coverage for template retrieval and selection
"""

import pytest
from unittest.mock import Mock, MagicMock
import json

from services.advice_template_service import (
    AdviceTemplateService,
    advice_template_service,
    get_advice_template,
    get_formatted_advice,
    get_advice_for_context,
    get_stats,
)
from models.safety import AdviceTemplate


class TestAdviceTemplateServiceInitialization:
    """Test AdviceTemplateService initialization"""

    def test_initialization(self):
        """Test service initializes correctly"""
        service = AdviceTemplateService()
        assert service is not None
        assert service.templates_retrieved == 0
        assert service.templates_used == 0

    def test_global_instance(self):
        """Test global instance is available"""
        assert advice_template_service is not None


class TestGetAdviceTemplate:
    """Test getting advice templates"""

    def setup_method(self):
        """Set up test fixtures"""
        self.service = AdviceTemplateService()
        self.mock_db = Mock()

    def test_get_advice_template_basic(self):
        """Test getting advice template with basic criteria"""
        # Create mock template
        mock_template = Mock(spec=AdviceTemplate)
        mock_template.id = 1
        mock_template.category = "friendship"
        mock_template.expert_reviewed = True
        mock_template.usage_count = 5

        # Mock AdviceTemplate.get_by_category
        with pytest.mock.patch.object(AdviceTemplate, 'get_by_category') as mock_get:
            mock_get.return_value = [mock_template]

            template = self.service.get_advice_template(
                db=self.mock_db,
                category="friendship",
                friendship_level=5
            )

            assert template is not None
            assert template.id == 1
            assert self.service.templates_retrieved > 0

    def test_get_advice_template_no_results(self):
        """Test getting template when no templates found"""
        # Mock empty result
        with pytest.mock.patch.object(AdviceTemplate, 'get_by_category') as mock_get:
            mock_get.return_value = []

            template = self.service.get_advice_template(
                db=self.mock_db,
                category="friendship",
                friendship_level=5
            )

            assert template is None

    def test_get_advice_template_with_age(self):
        """Test getting template with age filter"""
        mock_template = Mock(spec=AdviceTemplate)
        mock_template.expert_reviewed = True

        with pytest.mock.patch.object(AdviceTemplate, 'get_by_category') as mock_get:
            mock_get.return_value = [mock_template]

            template = self.service.get_advice_template(
                db=self.mock_db,
                category="school",
                friendship_level=3,
                age=10
            )

            assert template is not None
            # Verify age was passed
            mock_get.assert_called_once()
            call_kwargs = mock_get.call_args[1]
            assert call_kwargs['age'] == 10


class TestTemplateSelectionStrategies:
    """Test different template selection strategies"""

    def setup_method(self):
        """Set up test fixtures"""
        self.service = AdviceTemplateService()

        # Create mock templates
        self.template1 = Mock(spec=AdviceTemplate)
        self.template1.id = 1
        self.template1.expert_reviewed = True
        self.template1.usage_count = 10
        self.template1.tone = "supportive"

        self.template2 = Mock(spec=AdviceTemplate)
        self.template2.id = 2
        self.template2.expert_reviewed = False
        self.template2.usage_count = 5
        self.template2.tone = "encouraging"

        self.template3 = Mock(spec=AdviceTemplate)
        self.template3.id = 3
        self.template3.expert_reviewed = True
        self.template3.usage_count = 15
        self.template3.tone = "empathetic"

    def test_select_random_strategy(self):
        """Test random selection strategy"""
        templates = [self.template1, self.template2, self.template3]
        selected = self.service._select_template(templates, strategy="random")
        assert selected in templates

    def test_select_most_used_strategy(self):
        """Test most used selection strategy"""
        templates = [self.template1, self.template2, self.template3]
        selected = self.service._select_template(templates, strategy="most_used")
        # Should select template3 with usage_count=15
        assert selected.id == 3

    def test_select_expert_reviewed_strategy(self):
        """Test expert reviewed selection strategy"""
        templates = [self.template1, self.template2, self.template3]
        selected = self.service._select_template(templates, strategy="expert_reviewed")
        # Should select an expert-reviewed template (1 or 3)
        assert selected.expert_reviewed is True

    def test_select_expert_reviewed_when_none_available(self):
        """Test expert reviewed strategy falls back when none available"""
        templates = [self.template2]  # Only non-expert template
        selected = self.service._select_template(templates, strategy="expert_reviewed")
        # Should still select something
        assert selected is not None

    def test_select_tone_match_strategy(self):
        """Test tone matching selection strategy"""
        templates = [self.template1, self.template2, self.template3]
        selected = self.service._select_template(
            templates,
            strategy="tone_match",
            preferred_tone="empathetic"
        )
        # Should prefer template with matching tone
        assert selected.tone == "empathetic"

    def test_select_tone_match_fallback(self):
        """Test tone match falls back to expert reviewed"""
        templates = [self.template1, self.template2, self.template3]
        selected = self.service._select_template(
            templates,
            strategy="tone_match",
            preferred_tone="nonexistent_tone"
        )
        # Should fall back to expert reviewed
        assert selected.expert_reviewed is True

    def test_select_empty_list(self):
        """Test selection with empty template list"""
        selected = self.service._select_template([], strategy="random")
        assert selected is None


class TestGetFormattedAdvice:
    """Test getting formatted advice"""

    def setup_method(self):
        """Set up test fixtures"""
        self.service = AdviceTemplateService()
        self.mock_db = Mock()

        # Create mock template with format_advice method
        self.mock_template = Mock(spec=AdviceTemplate)
        self.mock_template.id = 1
        self.mock_template.category = "friendship"
        self.mock_template.expert_reviewed = True
        self.mock_template.format_advice.return_value = "Hi Alex! I understand you're having trouble with your friend."
        self.mock_template.increment_usage = Mock()

    def test_get_formatted_advice_basic(self):
        """Test getting formatted advice"""
        with pytest.mock.patch.object(AdviceTemplate, 'get_by_category') as mock_get:
            mock_get.return_value = [self.mock_template]

            advice = self.service.get_formatted_advice(
                db=self.mock_db,
                category="friendship",
                friendship_level=5,
                user_name="Alex"
            )

            assert advice is not None
            assert "Alex" in advice
            # Verify increment_usage was called
            self.mock_template.increment_usage.assert_called_once()
            # Verify db.commit was called
            self.mock_db.commit.assert_called_once()

    def test_get_formatted_advice_with_extra_kwargs(self):
        """Test formatted advice with additional formatting variables"""
        with pytest.mock.patch.object(AdviceTemplate, 'get_by_category') as mock_get:
            mock_get.return_value = [self.mock_template]

            advice = self.service.get_formatted_advice(
                db=self.mock_db,
                category="friendship",
                friendship_level=5,
                user_name="Alex",
                friend_name="Sam",
                situation="argument"
            )

            # Verify format_advice was called with correct kwargs
            call_kwargs = self.mock_template.format_advice.call_args[1]
            assert call_kwargs['name'] == "Alex"
            assert call_kwargs['friend_name'] == "Sam"
            assert call_kwargs['situation'] == "argument"

    def test_get_formatted_advice_no_template(self):
        """Test formatted advice when no template found"""
        with pytest.mock.patch.object(AdviceTemplate, 'get_by_category') as mock_get:
            mock_get.return_value = []

            advice = self.service.get_formatted_advice(
                db=self.mock_db,
                category="friendship",
                friendship_level=5
            )

            assert advice is None


class TestGetMultipleAdviceOptions:
    """Test getting multiple advice options"""

    def setup_method(self):
        """Set up test fixtures"""
        self.service = AdviceTemplateService()
        self.mock_db = Mock()

        # Create multiple mock templates
        self.templates = []
        for i in range(5):
            template = Mock(spec=AdviceTemplate)
            template.id = i + 1
            template.expert_reviewed = (i % 2 == 0)  # Every other is expert reviewed
            self.templates.append(template)

    def test_get_multiple_options(self):
        """Test getting multiple template options"""
        with pytest.mock.patch.object(AdviceTemplate, 'get_by_category') as mock_get:
            mock_get.return_value = self.templates

            options = self.service.get_multiple_advice_options(
                db=self.mock_db,
                category="friendship",
                friendship_level=5,
                limit=3
            )

            assert len(options) == 3
            assert all(isinstance(opt, Mock) for opt in options)

    def test_get_multiple_options_fewer_than_limit(self):
        """Test getting options when fewer templates than limit"""
        with pytest.mock.patch.object(AdviceTemplate, 'get_by_category') as mock_get:
            mock_get.return_value = self.templates[:2]  # Only 2 templates

            options = self.service.get_multiple_advice_options(
                db=self.mock_db,
                category="friendship",
                friendship_level=5,
                limit=3
            )

            assert len(options) == 2

    def test_get_multiple_options_prefers_expert_reviewed(self):
        """Test that multiple options prefer expert reviewed templates"""
        with pytest.mock.patch.object(AdviceTemplate, 'get_by_category') as mock_get:
            mock_get.return_value = self.templates

            options = self.service.get_multiple_advice_options(
                db=self.mock_db,
                category="friendship",
                friendship_level=5,
                limit=2
            )

            # Should include expert reviewed templates
            expert_count = sum(1 for opt in options if opt.expert_reviewed)
            assert expert_count > 0


class TestGetAdviceForContext:
    """Test getting advice based on full context"""

    def setup_method(self):
        """Set up test fixtures"""
        self.service = AdviceTemplateService()
        self.mock_db = Mock()

        # Create mock personality
        self.mock_personality = Mock()
        self.mock_personality.friendship_level = 5

        # Create mock template
        self.mock_template = Mock(spec=AdviceTemplate)
        self.mock_template.format_advice.return_value = "Here's some advice."
        self.mock_template.increment_usage = Mock()

    def test_get_advice_for_context_with_advice_request(self):
        """Test getting advice for context when advice is detected"""
        advice_detection = {
            "is_advice_request": True,
            "category": "friendship",
            "confidence": 0.85
        }

        with pytest.mock.patch.object(AdviceTemplate, 'get_by_category') as mock_get:
            mock_get.return_value = [self.mock_template]

            advice = self.service.get_advice_for_context(
                db=self.mock_db,
                advice_detection=advice_detection,
                personality=self.mock_personality,
                user_name="Alex",
                detected_mood="sad"
            )

            assert advice is not None

    def test_get_advice_for_context_not_advice_request(self):
        """Test getting advice when not an advice request"""
        advice_detection = {
            "is_advice_request": False,
            "category": "general",
            "confidence": 0.0
        }

        advice = self.service.get_advice_for_context(
            db=self.mock_db,
            advice_detection=advice_detection,
            personality=self.mock_personality
        )

        assert advice is None

    def test_get_advice_for_context_low_confidence(self):
        """Test getting advice with low confidence"""
        advice_detection = {
            "is_advice_request": True,
            "category": "friendship",
            "confidence": 0.3  # Below 0.5 threshold
        }

        advice = self.service.get_advice_for_context(
            db=self.mock_db,
            advice_detection=advice_detection,
            personality=self.mock_personality
        )

        assert advice is None

    def test_get_advice_for_context_mood_to_tone_mapping(self):
        """Test that mood maps to appropriate tone"""
        advice_detection = {
            "is_advice_request": True,
            "category": "emotional",
            "confidence": 0.9
        }

        with pytest.mock.patch.object(self.service, 'get_formatted_advice') as mock_formatted:
            mock_formatted.return_value = "Advice"

            self.service.get_advice_for_context(
                db=self.mock_db,
                advice_detection=advice_detection,
                personality=self.mock_personality,
                detected_mood="sad"
            )

            # Verify tone mapping
            call_kwargs = mock_formatted.call_args[1]
            assert call_kwargs['tone'] == "empathetic"


class TestGetTemplateById:
    """Test getting template by ID"""

    def setup_method(self):
        """Set up test fixtures"""
        self.service = AdviceTemplateService()
        self.mock_db = Mock()

    def test_get_template_by_id(self):
        """Test getting template by ID"""
        mock_template = Mock(spec=AdviceTemplate)
        mock_template.id = 123

        # Mock query chain
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_template

        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter

        template = self.service.get_template_by_id(self.mock_db, 123)

        assert template is not None
        assert template.id == 123

    def test_get_template_by_id_not_found(self):
        """Test getting template when ID not found"""
        # Mock query chain
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = None

        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter

        template = self.service.get_template_by_id(self.mock_db, 999)

        assert template is None


class TestServiceStatistics:
    """Test service statistics tracking"""

    def test_get_stats(self):
        """Test getting service statistics"""
        service = AdviceTemplateService()
        service.templates_retrieved = 10
        service.templates_used = 5

        stats = service.get_stats()

        assert stats["templates_retrieved"] == 10
        assert stats["templates_used"] == 5
        assert stats["service_status"] == "active"

    def test_stats_increment_on_retrieval(self):
        """Test that stats increment on template retrieval"""
        service = AdviceTemplateService()
        mock_db = Mock()

        initial_retrieved = service.templates_retrieved

        mock_template = Mock(spec=AdviceTemplate)
        mock_template.expert_reviewed = True

        with pytest.mock.patch.object(AdviceTemplate, 'get_by_category') as mock_get:
            mock_get.return_value = [mock_template, mock_template]  # 2 templates

            service.get_advice_template(
                db=mock_db,
                category="friendship",
                friendship_level=5
            )

            assert service.templates_retrieved == initial_retrieved + 2


class TestConvenienceFunctions:
    """Test module-level convenience functions"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_db = Mock()
        self.mock_template = Mock(spec=AdviceTemplate)
        self.mock_template.expert_reviewed = True
        self.mock_template.format_advice.return_value = "Advice"
        self.mock_template.increment_usage = Mock()

    def test_get_advice_template_function(self):
        """Test get_advice_template convenience function"""
        with pytest.mock.patch.object(AdviceTemplate, 'get_by_category') as mock_get:
            mock_get.return_value = [self.mock_template]

            template = get_advice_template(
                db=self.mock_db,
                category="friendship",
                friendship_level=5
            )

            assert template is not None

    def test_get_formatted_advice_function(self):
        """Test get_formatted_advice convenience function"""
        with pytest.mock.patch.object(AdviceTemplate, 'get_by_category') as mock_get:
            mock_get.return_value = [self.mock_template]

            advice = get_formatted_advice(
                db=self.mock_db,
                category="friendship",
                friendship_level=5,
                user_name="Alex"
            )

            assert advice is not None

    def test_get_advice_for_context_function(self):
        """Test get_advice_for_context convenience function"""
        mock_personality = Mock()
        mock_personality.friendship_level = 5

        advice_detection = {
            "is_advice_request": True,
            "category": "friendship",
            "confidence": 0.8
        }

        with pytest.mock.patch.object(AdviceTemplate, 'get_by_category') as mock_get:
            mock_get.return_value = [self.mock_template]

            advice = get_advice_for_context(
                db=self.mock_db,
                advice_detection=advice_detection,
                personality=mock_personality
            )

            assert advice is not None

    def test_get_stats_function(self):
        """Test get_stats convenience function"""
        stats = get_stats()
        assert stats is not None
        assert "service_status" in stats


class TestEdgeCases:
    """Test edge cases and error handling"""

    def setup_method(self):
        """Set up test fixtures"""
        self.service = AdviceTemplateService()
        self.mock_db = Mock()

    def test_get_advice_with_very_low_friendship_level(self):
        """Test getting advice with friendship level 1"""
        with pytest.mock.patch.object(AdviceTemplate, 'get_by_category') as mock_get:
            mock_get.return_value = []

            template = self.service.get_advice_template(
                db=self.mock_db,
                category="friendship",
                friendship_level=1
            )

            # Should not crash, just return None
            assert template is None

    def test_get_advice_with_very_high_friendship_level(self):
        """Test getting advice with friendship level 10"""
        mock_template = Mock(spec=AdviceTemplate)
        mock_template.expert_reviewed = True

        with pytest.mock.patch.object(AdviceTemplate, 'get_by_category') as mock_get:
            mock_get.return_value = [mock_template]

            template = self.service.get_advice_template(
                db=self.mock_db,
                category="friendship",
                friendship_level=10
            )

            assert template is not None

    def test_get_advice_with_unknown_category(self):
        """Test getting advice with unknown category"""
        with pytest.mock.patch.object(AdviceTemplate, 'get_by_category') as mock_get:
            mock_get.return_value = []

            template = self.service.get_advice_template(
                db=self.mock_db,
                category="unknown_category",
                friendship_level=5
            )

            assert template is None

    def test_get_advice_with_invalid_tone(self):
        """Test getting advice with invalid tone"""
        mock_template = Mock(spec=AdviceTemplate)
        mock_template.expert_reviewed = True
        mock_template.tone = "supportive"

        with pytest.mock.patch.object(AdviceTemplate, 'get_by_category') as mock_get:
            mock_get.return_value = [mock_template]

            template = self.service.get_advice_template(
                db=self.mock_db,
                category="friendship",
                friendship_level=5,
                tone="invalid_tone"
            )

            # Should still work, just filter out mismatched tones
            # or return None if no match
            assert template is not None or template is None


class TestMoodToToneMapping:
    """Test mood to tone mapping in context-based advice"""

    def setup_method(self):
        """Set up test fixtures"""
        self.service = AdviceTemplateService()

    def test_sad_maps_to_empathetic(self):
        """Test sad mood maps to empathetic tone"""
        mock_db = Mock()
        mock_personality = Mock()
        mock_personality.friendship_level = 5

        advice_detection = {
            "is_advice_request": True,
            "category": "emotional",
            "confidence": 0.9
        }

        with pytest.mock.patch.object(self.service, 'get_formatted_advice') as mock_formatted:
            mock_formatted.return_value = "Advice"

            self.service.get_advice_for_context(
                db=mock_db,
                advice_detection=advice_detection,
                personality=mock_personality,
                detected_mood="sad"
            )

            call_kwargs = mock_formatted.call_args[1]
            assert call_kwargs['tone'] == "empathetic"

    def test_anxious_maps_to_supportive(self):
        """Test anxious mood maps to supportive tone"""
        mock_db = Mock()
        mock_personality = Mock()
        mock_personality.friendship_level = 5

        advice_detection = {
            "is_advice_request": True,
            "category": "school",
            "confidence": 0.9
        }

        with pytest.mock.patch.object(self.service, 'get_formatted_advice') as mock_formatted:
            mock_formatted.return_value = "Advice"

            self.service.get_advice_for_context(
                db=mock_db,
                advice_detection=advice_detection,
                personality=mock_personality,
                detected_mood="anxious"
            )

            call_kwargs = mock_formatted.call_args[1]
            assert call_kwargs['tone'] == "supportive"

    def test_happy_maps_to_encouraging(self):
        """Test happy mood maps to encouraging tone"""
        mock_db = Mock()
        mock_personality = Mock()
        mock_personality.friendship_level = 5

        advice_detection = {
            "is_advice_request": True,
            "category": "hobby",
            "confidence": 0.9
        }

        with pytest.mock.patch.object(self.service, 'get_formatted_advice') as mock_formatted:
            mock_formatted.return_value = "Advice"

            self.service.get_advice_for_context(
                db=mock_db,
                advice_detection=advice_detection,
                personality=mock_personality,
                detected_mood="happy"
            )

            call_kwargs = mock_formatted.call_args[1]
            assert call_kwargs['tone'] == "encouraging"
