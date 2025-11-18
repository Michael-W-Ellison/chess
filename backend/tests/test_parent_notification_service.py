"""
Tests for Parent Notification Service
Comprehensive test coverage for parent notification system
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime

from services.parent_notification_service import (
    ParentNotificationService,
    parent_notification_service,
    notify_crisis_event,
    notify_high_severity_event,
    get_notification_history,
    get_stats,
)


class TestParentNotificationServiceInitialization:
    """Test ParentNotificationService initialization"""

    def test_initialization(self):
        """Test service initializes correctly"""
        service = ParentNotificationService()
        assert service is not None
        assert service.notification_count == 0

    def test_global_instance(self):
        """Test global instance is available"""
        assert parent_notification_service is not None


class TestCrisisEventNotification:
    """Test crisis event notifications"""

    def setup_method(self):
        """Set up test fixtures"""
        self.service = ParentNotificationService()
        self.mock_db = Mock()

        # Mock user
        self.mock_user = Mock()
        self.mock_user.id = 1
        self.mock_user.name = "TestChild"

        # Mock query result
        self.mock_db.query.return_value.filter.return_value.first.return_value = (
            self.mock_user
        )

    def test_notify_crisis_event_suicide(self):
        """Test notification for suicide crisis"""
        safety_result = {
            "safe": False,
            "flags": ["crisis"],
            "severity": "critical",
            "details": {
                "crisis": {
                    "detected": True,
                    "primary_category": "suicide",
                    "keywords_found": [{"keyword": "kill myself", "category": "suicide"}],
                }
            },
            "original_message": "I want to kill myself",
            "notify_parent": True,
        }

        result = self.service.notify_crisis_event(
            user_id=1, conversation_id=100, safety_result=safety_result, db=self.mock_db
        )

        assert result["success"] is True
        assert result["category"] == "crisis_suicide"
        assert result["severity"] == "critical"
        assert result["notification_sent"] is True

    def test_notify_crisis_event_self_harm(self):
        """Test notification for self-harm crisis"""
        safety_result = {
            "flags": ["crisis"],
            "severity": "critical",
            "details": {
                "crisis": {
                    "detected": True,
                    "primary_category": "self_harm",
                }
            },
            "original_message": "I cut myself",
            "notify_parent": True,
        }

        result = self.service.notify_crisis_event(
            user_id=1, conversation_id=100, safety_result=safety_result, db=self.mock_db
        )

        assert result["success"] is True
        assert result["category"] == "crisis_self_harm"

    def test_notify_abuse_physical(self):
        """Test notification for physical abuse"""
        safety_result = {
            "flags": ["abuse"],
            "severity": "critical",
            "details": {
                "crisis": {
                    "detected": True,
                    "primary_category": "abuse_physical",
                }
            },
            "original_message": "My dad hits me",
            "notify_parent": True,
        }

        result = self.service.notify_crisis_event(
            user_id=1, conversation_id=100, safety_result=safety_result, db=self.mock_db
        )

        assert result["success"] is True
        assert result["category"] == "abuse_physical"

    def test_notify_abuse_emotional(self):
        """Test notification for emotional abuse"""
        safety_result = {
            "flags": ["abuse"],
            "severity": "critical",
            "details": {
                "crisis": {
                    "detected": True,
                    "primary_category": "abuse_emotional",
                }
            },
            "original_message": "My mom threatens me",
            "notify_parent": True,
        }

        result = self.service.notify_crisis_event(
            user_id=1, conversation_id=100, safety_result=safety_result, db=self.mock_db
        )

        assert result["success"] is True
        assert result["category"] == "abuse_emotional"

    def test_notify_abuse_sexual(self):
        """Test notification for sexual abuse"""
        safety_result = {
            "flags": ["abuse"],
            "severity": "critical",
            "details": {
                "crisis": {
                    "detected": True,
                    "primary_category": "abuse_sexual",
                }
            },
            "original_message": "Someone touched me inappropriately",
            "notify_parent": True,
        }

        result = self.service.notify_crisis_event(
            user_id=1, conversation_id=100, safety_result=safety_result, db=self.mock_db
        )

        assert result["success"] is True
        assert result["category"] == "abuse_sexual"

    def test_notify_user_not_found(self):
        """Test notification when user not found"""
        # Mock user not found
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        safety_result = {
            "flags": ["crisis"],
            "severity": "critical",
            "details": {"crisis": {"primary_category": "suicide"}},
            "original_message": "test",
        }

        result = self.service.notify_crisis_event(
            user_id=999, conversation_id=100, safety_result=safety_result, db=self.mock_db
        )

        assert result["success"] is False
        assert "error" in result


class TestHighSeverityNotification:
    """Test high-severity (non-crisis) event notifications"""

    def setup_method(self):
        """Set up test fixtures"""
        self.service = ParentNotificationService()
        self.mock_db = Mock()

        # Mock user
        self.mock_user = Mock()
        self.mock_user.id = 1
        self.mock_user.name = "TestChild"

        self.mock_db.query.return_value.filter.return_value.first.return_value = (
            self.mock_user
        )

    def test_notify_high_severity_event(self):
        """Test notification for high-severity (non-crisis) event"""
        safety_result = {
            "flags": ["profanity"],
            "severity": "high",
            "original_message": "test message with severe profanity",
            "notify_parent": True,
        }

        result = self.service.notify_high_severity_event(
            user_id=1, conversation_id=100, safety_result=safety_result, db=self.mock_db
        )

        assert result["success"] is True
        assert result["category"] == "high_severity_content"
        assert result["severity"] == "high"


class TestNotificationCategoryDetermination:
    """Test notification category determination logic"""

    def setup_method(self):
        """Set up test fixtures"""
        self.service = ParentNotificationService()

    def test_get_notification_category_suicide(self):
        """Test category determination for suicide crisis"""
        flags = ["crisis"]
        details = {"crisis": {"primary_category": "suicide"}}

        category = self.service._get_notification_category(flags, details)
        assert category == "crisis_suicide"

    def test_get_notification_category_self_harm(self):
        """Test category determination for self-harm crisis"""
        flags = ["crisis"]
        details = {"crisis": {"primary_category": "self_harm"}}

        category = self.service._get_notification_category(flags, details)
        assert category == "crisis_self_harm"

    def test_get_notification_category_abuse_physical(self):
        """Test category determination for physical abuse"""
        flags = ["abuse"]
        details = {"crisis": {"primary_category": "abuse_physical"}}

        category = self.service._get_notification_category(flags, details)
        assert category == "abuse_physical"

    def test_get_notification_category_abuse_emotional(self):
        """Test category determination for emotional abuse"""
        flags = ["abuse"]
        details = {"crisis": {"primary_category": "abuse_emotional"}}

        category = self.service._get_notification_category(flags, details)
        assert category == "abuse_emotional"

    def test_get_notification_category_abuse_sexual(self):
        """Test category determination for sexual abuse"""
        flags = ["abuse"]
        details = {"crisis": {"primary_category": "abuse_sexual"}}

        category = self.service._get_notification_category(flags, details)
        assert category == "abuse_sexual"

    def test_get_notification_category_inappropriate(self):
        """Test category determination for inappropriate content"""
        flags = ["inappropriate_request"]
        details = {}

        category = self.service._get_notification_category(flags, details)
        assert category == "inappropriate_content"

    def test_get_notification_category_profanity(self):
        """Test category determination for severe profanity"""
        flags = ["profanity"]
        details = {}

        category = self.service._get_notification_category(flags, details)
        assert category == "severe_language"


class TestNotificationMessageFormatting:
    """Test notification message formatting"""

    def setup_method(self):
        """Set up test fixtures"""
        self.service = ParentNotificationService()

    def test_format_suicide_notification(self):
        """Test formatting of suicide crisis notification"""
        message = self.service._format_crisis_notification(
            user_name="TestChild",
            category="crisis_suicide",
            severity="critical",
            details={},
            timestamp=datetime(2023, 10, 15, 14, 30),
        )

        assert "URGENT" in message
        assert "Suicide-Related Content" in message
        assert "TestChild" in message
        assert "988" in message
        assert "CRITICAL" in message

    def test_format_self_harm_notification(self):
        """Test formatting of self-harm notification"""
        message = self.service._format_crisis_notification(
            user_name="TestChild",
            category="crisis_self_harm",
            severity="critical",
            details={},
            timestamp=datetime.now(),
        )

        assert "Self-Harm" in message
        assert "741741" in message

    def test_format_physical_abuse_notification(self):
        """Test formatting of physical abuse notification"""
        message = self.service._format_crisis_notification(
            user_name="TestChild",
            category="abuse_physical",
            severity="critical",
            details={},
            timestamp=datetime.now(),
        )

        assert "Physical Abuse" in message
        assert "1-800-422-4453" in message
        assert "911" in message

    def test_format_emotional_abuse_notification(self):
        """Test formatting of emotional abuse notification"""
        message = self.service._format_crisis_notification(
            user_name="TestChild",
            category="abuse_emotional",
            severity="critical",
            details={},
            timestamp=datetime.now(),
        )

        assert "Emotional Abuse" in message
        assert "1-800-422-4453" in message

    def test_format_sexual_abuse_notification(self):
        """Test formatting of sexual abuse notification"""
        message = self.service._format_crisis_notification(
            user_name="TestChild",
            category="abuse_sexual",
            severity="critical",
            details={},
            timestamp=datetime.now(),
        )

        assert "Sexual Abuse" in message
        assert "1-800-422-4453" in message
        assert "1-800-656-4673" in message or "RAINN" in message

    def test_notification_message_includes_timestamp(self):
        """Test that notification includes formatted timestamp"""
        message = self.service._format_crisis_notification(
            user_name="TestChild",
            category="crisis_suicide",
            severity="critical",
            details={},
            timestamp=datetime(2023, 10, 15, 14, 30),
        )

        assert "2023-10-15" in message or "Time:" in message

    def test_notification_message_includes_recommended_action(self):
        """Test that notification includes recommended action"""
        message = self.service._format_crisis_notification(
            user_name="TestChild",
            category="crisis_suicide",
            severity="critical",
            details={},
            timestamp=datetime.now(),
        )

        assert "RECOMMENDED ACTION" in message or "ACTION" in message


class TestNotificationHistory:
    """Test notification history retrieval"""

    def setup_method(self):
        """Set up test fixtures"""
        self.service = ParentNotificationService()
        self.mock_db = Mock()

    def test_get_notification_history_empty(self):
        """Test getting notification history when no notifications exist"""
        # Mock empty result
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
            []
        )

        history = self.service.get_notification_history(user_id=1, db=self.mock_db)
        assert history == []

    def test_get_notification_history_with_records(self):
        """Test getting notification history with records"""
        # Mock safety flags
        mock_flag1 = Mock()
        mock_flag1.timestamp = datetime.now()
        mock_flag1.severity = "critical"
        mock_flag1.flag_type = "crisis"
        mock_flag1.content_snippet = "test message"
        mock_flag1.action_taken = "crisis_response"

        mock_flag2 = Mock()
        mock_flag2.timestamp = datetime.now()
        mock_flag2.severity = "high"
        mock_flag2.flag_type = "profanity"
        mock_flag2.content_snippet = "test message 2"
        mock_flag2.action_taken = "block_with_education"

        self.mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
            [mock_flag1, mock_flag2]
        )

        history = self.service.get_notification_history(user_id=1, db=self.mock_db)

        assert len(history) == 2
        assert history[0]["severity"] == "critical"
        assert history[0]["flag_type"] == "crisis"
        assert history[1]["severity"] == "high"


class TestServiceStatistics:
    """Test service statistics"""

    def test_get_stats(self):
        """Test getting service statistics"""
        service = ParentNotificationService()

        # Send some notifications
        service.notification_count = 5

        stats = service.get_stats()

        assert "notifications_sent_session" in stats
        assert stats["notifications_sent_session"] == 5
        assert "service_status" in stats
        assert stats["service_status"] == "active"


class TestConvenienceFunctions:
    """Test module-level convenience functions"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_db = Mock()

        # Mock user
        self.mock_user = Mock()
        self.mock_user.id = 1
        self.mock_user.name = "TestChild"

        self.mock_db.query.return_value.filter.return_value.first.return_value = (
            self.mock_user
        )

    def test_notify_crisis_event_function(self):
        """Test notify_crisis_event convenience function"""
        safety_result = {
            "flags": ["crisis"],
            "severity": "critical",
            "details": {"crisis": {"primary_category": "suicide"}},
            "original_message": "test",
        }

        result = notify_crisis_event(
            user_id=1, conversation_id=100, safety_result=safety_result, db=self.mock_db
        )

        assert result is not None
        assert "success" in result

    def test_notify_high_severity_event_function(self):
        """Test notify_high_severity_event convenience function"""
        safety_result = {
            "flags": ["profanity"],
            "severity": "high",
            "original_message": "test",
        }

        result = notify_high_severity_event(
            user_id=1, conversation_id=100, safety_result=safety_result, db=self.mock_db
        )

        assert result is not None
        assert "success" in result

    def test_get_notification_history_function(self):
        """Test get_notification_history convenience function"""
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
            []
        )

        history = get_notification_history(user_id=1, db=self.mock_db)
        assert history is not None
        assert isinstance(history, list)

    def test_get_stats_function(self):
        """Test get_stats convenience function"""
        stats = get_stats()
        assert stats is not None
        assert "service_status" in stats


class TestNotificationIncrement:
    """Test notification count increments"""

    def setup_method(self):
        """Set up test fixtures"""
        self.service = ParentNotificationService()
        self.mock_db = Mock()

        # Mock user
        self.mock_user = Mock()
        self.mock_user.id = 1
        self.mock_user.name = "TestChild"

        self.mock_db.query.return_value.filter.return_value.first.return_value = (
            self.mock_user
        )

    def test_notification_count_increments(self):
        """Test that notification count increments with each notification"""
        initial_count = self.service.notification_count

        safety_result = {
            "flags": ["crisis"],
            "severity": "critical",
            "details": {"crisis": {"primary_category": "suicide"}},
            "original_message": "test",
        }

        self.service.notify_crisis_event(
            user_id=1, conversation_id=100, safety_result=safety_result, db=self.mock_db
        )

        assert self.service.notification_count == initial_count + 1

        self.service.notify_crisis_event(
            user_id=1, conversation_id=101, safety_result=safety_result, db=self.mock_db
        )

        assert self.service.notification_count == initial_count + 2
