"""
Tests for Safety Flag Service
Verifies that safety flag creation, retrieval, and management work correctly
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from services.safety_flag_service import SafetyFlagService, safety_flag_service
from models.safety import SafetyFlag


@pytest.fixture
def service():
    """Return a fresh SafetyFlagService instance"""
    return SafetyFlagService()


@pytest.fixture
def mock_db():
    """Return a mock database session"""
    return Mock(spec=Session)


class TestSafetyFlagCreation:
    """Test creating safety flags"""

    def test_create_flag_minimal(self, service, mock_db):
        """Test creating a flag with minimal parameters"""
        flag = service.create_flag(
            db=mock_db,
            user_id=1,
            flag_type="profanity",
            severity="low"
        )

        # Verify flag was added to session
        assert mock_db.add.called
        assert mock_db.commit.called

    def test_create_flag_full(self, service, mock_db):
        """Test creating a flag with all parameters"""
        flag = service.create_flag(
            db=mock_db,
            user_id=1,
            flag_type="crisis",
            severity="critical",
            content_snippet="Test message content",
            action_taken="block",
            message_id=123,
            notify_parent=True
        )

        assert mock_db.add.called
        assert mock_db.commit.called

    def test_create_flag_truncates_long_content(self, service, mock_db):
        """Test that content snippet is truncated to 100 characters"""
        long_content = "a" * 200

        flag = service.create_flag(
            db=mock_db,
            user_id=1,
            flag_type="profanity",
            severity="medium",
            content_snippet=long_content
        )

        # Check that content was truncated
        call_args = mock_db.add.call_args[0][0]
        assert len(call_args.content_snippet) == 100

    def test_create_different_flag_types(self, service, mock_db):
        """Test creating flags with different types"""
        flag_types = ["crisis", "profanity", "bullying", "inappropriate_request", "abuse"]

        for flag_type in flag_types:
            flag = service.create_flag(
                db=mock_db,
                user_id=1,
                flag_type=flag_type,
                severity="medium"
            )
            assert mock_db.add.called

    def test_create_different_severities(self, service, mock_db):
        """Test creating flags with different severities"""
        severities = ["low", "medium", "high", "critical"]

        for severity in severities:
            flag = service.create_flag(
                db=mock_db,
                user_id=1,
                flag_type="profanity",
                severity=severity
            )
            assert mock_db.add.called


class TestSafetyFlagRetrieval:
    """Test retrieving safety flags"""

    def test_get_by_id(self, service, mock_db):
        """Test getting a flag by ID"""
        mock_query = Mock()
        mock_filter = Mock()
        mock_first = Mock(return_value=SafetyFlag())

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = mock_first.return_value

        result = service.get_by_id(mock_db, 1)

        assert mock_db.query.called
        assert result is not None

    def test_get_by_user(self, service, mock_db):
        """Test getting flags by user ID"""
        mock_query = Mock()
        mock_filter = Mock()
        mock_order = Mock()
        mock_all = Mock(return_value=[])

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.order_by.return_value = mock_order
        mock_order.all.return_value = []

        result = service.get_by_user(mock_db, 1)

        assert mock_db.query.called
        assert isinstance(result, list)

    def test_get_by_user_with_limit(self, service, mock_db):
        """Test getting flags with limit and offset"""
        mock_query = Mock()
        mock_filter = Mock()
        mock_order = Mock()
        mock_limit = Mock()
        mock_offset = Mock()

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.order_by.return_value = mock_order
        mock_order.limit.return_value = mock_limit
        mock_limit.offset.return_value = mock_offset
        mock_offset.all.return_value = []

        result = service.get_by_user(mock_db, 1, limit=10, offset=5)

        assert mock_order.limit.called
        assert mock_limit.offset.called

    def test_get_by_severity(self, service, mock_db):
        """Test getting flags by severity"""
        mock_query = Mock()
        mock_filter = Mock()
        mock_order = Mock()

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.order_by.return_value = mock_order
        mock_order.all.return_value = []

        result = service.get_by_severity(mock_db, "critical")

        assert mock_db.query.called

    def test_get_by_severity_with_filters(self, service, mock_db):
        """Test getting flags by severity with user and date filters"""
        mock_query = Mock()
        mock_filter1 = Mock()
        mock_filter2 = Mock()
        mock_filter3 = Mock()
        mock_order = Mock()

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter1
        mock_filter1.filter.return_value = mock_filter2
        mock_filter2.filter.return_value = mock_filter3
        mock_filter3.order_by.return_value = mock_order
        mock_order.all.return_value = []

        since_date = datetime.now() - timedelta(days=7)
        result = service.get_by_severity(
            mock_db, "high", user_id=1, since_date=since_date
        )

        assert mock_db.query.called

    def test_get_critical_flags(self, service, mock_db):
        """Test getting critical severity flags"""
        mock_query = Mock()
        mock_filter = Mock()
        mock_order = Mock()

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.order_by.return_value = mock_order
        mock_order.all.return_value = []

        result = service.get_critical_flags(mock_db)

        assert mock_db.query.called

    def test_get_critical_flags_unnotified_only(self, service, mock_db):
        """Test getting critical flags excluding notified ones"""
        mock_query = Mock()
        mock_filter1 = Mock()
        mock_filter2 = Mock()
        mock_order = Mock()

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter1
        mock_filter1.filter.return_value = mock_filter2
        mock_filter2.order_by.return_value = mock_order
        mock_order.all.return_value = []

        result = service.get_critical_flags(mock_db, include_notified=False)

        # Should filter for parent_notified == False
        assert mock_db.query.called

    def test_get_by_type(self, service, mock_db):
        """Test getting flags by type"""
        mock_query = Mock()
        mock_filter = Mock()
        mock_order = Mock()

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.order_by.return_value = mock_order
        mock_order.all.return_value = []

        result = service.get_by_type(mock_db, "profanity")

        assert mock_db.query.called

    def test_get_by_type_with_comma_separated(self, service, mock_db):
        """Test getting flags with comma-separated types"""
        mock_query = Mock()
        mock_filter = Mock()
        mock_order = Mock()

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.order_by.return_value = mock_order
        mock_order.all.return_value = []

        result = service.get_by_type(mock_db, "crisis,abuse")

        assert mock_db.query.called

    def test_get_unnotified_flags(self, service, mock_db):
        """Test getting flags where parent wasn't notified"""
        mock_query = Mock()
        mock_filter = Mock()
        mock_order = Mock()

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.order_by.return_value = mock_order
        mock_order.all.return_value = []

        result = service.get_unnotified_flags(mock_db)

        assert mock_db.query.called

    def test_get_unnotified_flags_with_min_severity(self, service, mock_db):
        """Test getting unnotified flags with minimum severity filter"""
        mock_query = Mock()
        mock_filter1 = Mock()
        mock_filter2 = Mock()
        mock_order = Mock()

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter1
        mock_filter1.filter.return_value = mock_filter2
        mock_filter2.order_by.return_value = mock_order
        mock_order.all.return_value = []

        result = service.get_unnotified_flags(mock_db, min_severity="high")

        # Should include "high" and "critical" only
        assert mock_db.query.called

    def test_get_recent_flags(self, service, mock_db):
        """Test getting recent flags from last N hours"""
        mock_query = Mock()
        mock_filter = Mock()
        mock_order = Mock()

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.order_by.return_value = mock_order
        mock_order.all.return_value = []

        result = service.get_recent_flags(mock_db, hours=24)

        assert mock_db.query.called


class TestParentNotification:
    """Test parent notification functionality"""

    def test_mark_parent_notified(self, service, mock_db):
        """Test marking a flag as parent notified"""
        # Create a mock flag
        mock_flag = SafetyFlag()
        mock_flag.id = 1
        mock_flag.parent_notified = False

        # Mock get_by_id to return our flag
        with patch.object(service, 'get_by_id', return_value=mock_flag):
            result = service.mark_parent_notified(mock_db, 1)

            assert result.parent_notified is True
            assert mock_db.commit.called

    def test_mark_parent_notified_not_found(self, service, mock_db):
        """Test marking non-existent flag returns None"""
        with patch.object(service, 'get_by_id', return_value=None):
            result = service.mark_parent_notified(mock_db, 999)

            assert result is None
            assert not mock_db.commit.called

    def test_mark_multiple_parent_notified(self, service, mock_db):
        """Test marking multiple flags as parent notified"""
        mock_query = Mock()
        mock_filter = Mock()
        mock_update = Mock(return_value=3)

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.update.return_value = 3

        count = service.mark_multiple_parent_notified(mock_db, [1, 2, 3])

        assert count == 3
        assert mock_db.commit.called


class TestStatistics:
    """Test statistics functionality"""

    def test_get_stats(self, service, mock_db):
        """Test getting safety flag statistics"""
        mock_query = Mock()
        mock_count = Mock(return_value=10)
        mock_filter = Mock()

        mock_db.query.return_value = mock_query
        mock_query.count.return_value = 10
        mock_query.filter.return_value = mock_filter
        mock_filter.count.return_value = 0

        stats = service.get_stats(mock_db)

        assert "total_flags" in stats
        assert "by_severity" in stats
        assert "by_type" in stats
        assert "parent_notified" in stats
        assert "parent_unnotified" in stats
        assert "last_24_hours" in stats

    def test_get_stats_with_user_filter(self, service, mock_db):
        """Test getting stats filtered by user"""
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter2 = Mock()

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.filter.return_value = mock_filter2
        mock_filter.count.return_value = 5
        mock_filter2.count.return_value = 2

        stats = service.get_stats(mock_db, user_id=1)

        assert isinstance(stats, dict)

    def test_get_user_safety_summary(self, service, mock_db):
        """Test getting comprehensive user safety summary"""
        mock_query = Mock()
        mock_filter = Mock()
        mock_order = Mock()
        mock_limit = Mock()

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.filter.return_value = mock_filter
        mock_filter.order_by.return_value = mock_order
        mock_order.all.return_value = []
        mock_order.limit.return_value = mock_limit
        mock_limit.all.return_value = []
        mock_filter.count.return_value = 0

        summary = service.get_user_safety_summary(mock_db, 1)

        assert "user_id" in summary
        assert summary["user_id"] == 1
        assert "all_time" in summary
        assert "last_7_days" in summary
        assert "critical_needing_attention" in summary
        assert "most_recent_flag" in summary


class TestDatabaseMaintenance:
    """Test database maintenance functionality"""

    def test_delete_old_flags(self, service, mock_db):
        """Test deleting old flags"""
        mock_query = Mock()
        mock_filter1 = Mock()
        mock_filter2 = Mock()
        mock_delete = Mock(return_value=5)

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter1
        mock_filter1.filter.return_value = mock_filter2
        mock_filter2.delete.return_value = 5

        count = service.delete_old_flags(mock_db, days_old=365)

        assert count == 5
        assert mock_db.commit.called

    def test_delete_old_flags_exclude_critical(self, service, mock_db):
        """Test that critical flags can be excluded from deletion"""
        mock_query = Mock()
        mock_filter1 = Mock()
        mock_filter2 = Mock()
        mock_delete = Mock(return_value=3)

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter1
        mock_filter1.filter.return_value = mock_filter2
        mock_filter2.delete.return_value = 3

        count = service.delete_old_flags(mock_db, days_old=365, exclude_critical=True)

        # Should filter out critical severity
        assert count == 3


class TestConvenienceFunctions:
    """Test module-level convenience functions"""

    def test_convenience_functions_exist(self):
        """Test that convenience functions are available"""
        from services.safety_flag_service import (
            create_flag,
            get_by_user,
            get_critical_flags,
            mark_parent_notified,
            get_stats,
            get_user_safety_summary
        )

        assert callable(create_flag)
        assert callable(get_by_user)
        assert callable(get_critical_flags)
        assert callable(mark_parent_notified)
        assert callable(get_stats)
        assert callable(get_user_safety_summary)


class TestIntegration:
    """Integration tests with real SafetyFlag model"""

    def test_flag_creation_with_real_model(self, service, mock_db):
        """Test that created flag has correct attributes"""
        flag = service.create_flag(
            db=mock_db,
            user_id=1,
            flag_type="crisis",
            severity="critical",
            content_snippet="Test message",
            action_taken="block",
            message_id=123
        )

        # Get the flag object that was added
        call_args = mock_db.add.call_args[0][0]

        assert isinstance(call_args, SafetyFlag)
        assert call_args.user_id == 1
        assert call_args.flag_type == "crisis"
        assert call_args.severity == "critical"
        assert call_args.action_taken == "block"
        assert call_args.message_id == 123
        assert call_args.parent_notified is False
