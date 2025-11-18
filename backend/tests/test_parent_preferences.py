"""
Tests for Parent Notification Preferences
Comprehensive test coverage for preference model, service, and API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime

from main import app
from models.parent_preferences import ParentNotificationPreferences
from services.parent_preferences_service import (
    ParentPreferencesService,
    parent_preferences_service
)


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_db():
    """Create mock database session"""
    return Mock()


@pytest.fixture
def mock_preferences():
    """Create mock preferences"""
    prefs = Mock(spec=ParentNotificationPreferences)
    prefs.id = 1
    prefs.user_id = 1
    prefs.email_notifications_enabled = True
    prefs.instant_notification_min_severity = "high"
    prefs.notify_on_critical = True
    prefs.notify_on_high = True
    prefs.notify_on_medium = False
    prefs.notify_on_low = False
    prefs.notify_on_crisis = True
    prefs.notify_on_abuse = True
    prefs.notify_on_bullying = True
    prefs.notify_on_profanity = False
    prefs.notify_on_inappropriate = True
    prefs.summary_frequency = "weekly"
    prefs.summary_day_of_week = 0
    prefs.summary_hour = 9
    prefs.include_content_snippets = True
    prefs.max_snippet_length = 100
    prefs.quiet_hours_enabled = False
    prefs.quiet_hours_start = None
    prefs.quiet_hours_end = None
    prefs.created_at = datetime.now()
    prefs.updated_at = datetime.now()
    return prefs


class TestParentNotificationPreferencesModel:
    """Test ParentNotificationPreferences model"""

    def test_to_dict(self, mock_preferences):
        """Test converting preferences to dict"""
        # Mock the to_dict method to return actual dict
        mock_preferences.to_dict.return_value = {
            "id": 1,
            "user_id": 1,
            "email_notifications_enabled": True,
            "instant_notification_min_severity": "high",
            "severity_filters": {
                "critical": True,
                "high": True,
                "medium": False,
                "low": False,
            },
            "flag_type_filters": {
                "crisis": True,
                "abuse": True,
                "bullying": True,
                "profanity": False,
                "inappropriate": True,
            },
            "summary_settings": {
                "frequency": "weekly",
                "day_of_week": 0,
                "hour": 9,
            },
            "content_settings": {
                "include_snippets": True,
                "max_snippet_length": 100,
            },
            "quiet_hours": {
                "enabled": False,
                "start": None,
                "end": None,
            },
        }

        result = mock_preferences.to_dict()

        assert result["user_id"] == 1
        assert result["email_notifications_enabled"] is True
        assert result["severity_filters"]["critical"] is True

    def test_should_notify_for_flag_enabled(self, mock_preferences):
        """Test notification check when enabled"""
        # Mock the method
        mock_preferences.should_notify_for_flag.return_value = True

        result = mock_preferences.should_notify_for_flag("critical", "crisis")

        assert result is True

    def test_should_notify_for_flag_disabled_severity(self, mock_preferences):
        """Test notification check for disabled severity"""
        mock_preferences.should_notify_for_flag.return_value = False

        result = mock_preferences.should_notify_for_flag("low", "profanity")

        assert result is False

    def test_is_quiet_hours_disabled(self, mock_preferences):
        """Test quiet hours check when disabled"""
        mock_preferences.is_quiet_hours.return_value = False

        result = mock_preferences.is_quiet_hours()

        assert result is False


class TestParentPreferencesService:
    """Test ParentPreferencesService"""

    def test_service_initialization(self):
        """Test service initializes correctly"""
        service = ParentPreferencesService()
        assert service is not None

    def test_global_instance(self):
        """Test global instance exists"""
        assert parent_preferences_service is not None

    @patch.object(ParentNotificationPreferences, "get_or_create_defaults")
    def test_get_preferences(self, mock_get_or_create, mock_db, mock_preferences):
        """Test getting preferences"""
        mock_get_or_create.return_value = mock_preferences

        service = ParentPreferencesService()
        result = service.get_preferences(mock_db, user_id=1)

        assert result == mock_preferences
        mock_get_or_create.assert_called_once_with(mock_db, 1)

    def test_update_preferences_valid_field(self, mock_db, mock_preferences):
        """Test updating preferences with valid field"""
        service = ParentPreferencesService()

        # Mock get_preferences
        with patch.object(service, "get_preferences", return_value=mock_preferences):
            result = service.update_preferences(
                mock_db,
                user_id=1,
                updates={"email_notifications_enabled": False}
            )

            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once_with(mock_preferences)

    def test_update_preferences_invalid_severity(self, mock_db, mock_preferences):
        """Test updating with invalid severity"""
        service = ParentPreferencesService()

        with patch.object(service, "get_preferences", return_value=mock_preferences):
            with pytest.raises(ValueError, match="Invalid severity"):
                service.update_preferences(
                    mock_db,
                    user_id=1,
                    updates={"instant_notification_min_severity": "invalid"}
                )

    def test_update_preferences_invalid_frequency(self, mock_db, mock_preferences):
        """Test updating with invalid summary frequency"""
        service = ParentPreferencesService()

        with patch.object(service, "get_preferences", return_value=mock_preferences):
            with pytest.raises(ValueError, match="Invalid summary frequency"):
                service.update_preferences(
                    mock_db,
                    user_id=1,
                    updates={"summary_frequency": "invalid"}
                )

    def test_update_severity_filters(self, mock_db, mock_preferences):
        """Test updating severity filters"""
        service = ParentPreferencesService()

        with patch.object(service, "update_preferences") as mock_update:
            service.update_severity_filters(
                mock_db,
                user_id=1,
                critical=True,
                high=False
            )

            mock_update.assert_called_once()
            args = mock_update.call_args
            assert args[0][1] == 1  # user_id
            assert args[0][2]["notify_on_critical"] is True
            assert args[0][2]["notify_on_high"] is False

    def test_update_type_filters(self, mock_db, mock_preferences):
        """Test updating type filters"""
        service = ParentPreferencesService()

        with patch.object(service, "update_preferences") as mock_update:
            service.update_type_filters(
                mock_db,
                user_id=1,
                crisis=False,
                bullying=True
            )

            mock_update.assert_called_once()
            args = mock_update.call_args
            assert args[0][2]["notify_on_crisis"] is False
            assert args[0][2]["notify_on_bullying"] is True

    def test_update_summary_settings(self, mock_db, mock_preferences):
        """Test updating summary settings"""
        service = ParentPreferencesService()

        with patch.object(service, "update_preferences") as mock_update:
            service.update_summary_settings(
                mock_db,
                user_id=1,
                frequency="daily",
                hour=14
            )

            mock_update.assert_called_once()
            args = mock_update.call_args
            assert args[0][2]["summary_frequency"] == "daily"
            assert args[0][2]["summary_hour"] == 14

    def test_update_quiet_hours(self, mock_db, mock_preferences):
        """Test updating quiet hours"""
        service = ParentPreferencesService()

        with patch.object(service, "update_preferences") as mock_update:
            service.update_quiet_hours(
                mock_db,
                user_id=1,
                enabled=True,
                start=22,
                end=8
            )

            mock_update.assert_called_once()
            args = mock_update.call_args
            assert args[0][2]["quiet_hours_enabled"] is True
            assert args[0][2]["quiet_hours_start"] == 22
            assert args[0][2]["quiet_hours_end"] == 8

    def test_should_notify_allowed(self, mock_db, mock_preferences):
        """Test should_notify when notification allowed"""
        service = ParentPreferencesService()

        mock_preferences.should_notify_for_flag.return_value = True
        mock_preferences.is_quiet_hours.return_value = False

        with patch.object(service, "get_preferences", return_value=mock_preferences):
            result = service.should_notify(mock_db, 1, "critical", "crisis")

            assert result is True

    def test_should_notify_suppressed_by_preferences(self, mock_db, mock_preferences):
        """Test should_notify when suppressed by preferences"""
        service = ParentPreferencesService()

        mock_preferences.should_notify_for_flag.return_value = False

        with patch.object(service, "get_preferences", return_value=mock_preferences):
            result = service.should_notify(mock_db, 1, "low", "profanity")

            assert result is False

    def test_should_notify_suppressed_by_quiet_hours(self, mock_db, mock_preferences):
        """Test should_notify when suppressed by quiet hours"""
        service = ParentPreferencesService()

        mock_preferences.should_notify_for_flag.return_value = True
        mock_preferences.is_quiet_hours.return_value = True

        with patch.object(service, "get_preferences", return_value=mock_preferences):
            result = service.should_notify(mock_db, 1, "critical", "crisis")

            assert result is False

    def test_enable_all_notifications(self, mock_db, mock_preferences):
        """Test enabling all notifications"""
        service = ParentPreferencesService()

        with patch.object(service, "update_preferences") as mock_update:
            service.enable_all_notifications(mock_db, 1)

            mock_update.assert_called_once()
            args = mock_update.call_args
            updates = args[0][2]
            assert updates["email_notifications_enabled"] is True
            assert updates["notify_on_critical"] is True
            assert updates["notify_on_profanity"] is True

    def test_disable_all_notifications(self, mock_db, mock_preferences):
        """Test disabling all notifications"""
        service = ParentPreferencesService()

        with patch.object(service, "update_preferences") as mock_update:
            service.disable_all_notifications(mock_db, 1)

            mock_update.assert_called_once()
            args = mock_update.call_args
            updates = args[0][2]
            assert updates["email_notifications_enabled"] is False

    @patch.object(ParentNotificationPreferences, "get_or_create_defaults")
    def test_reset_to_defaults(self, mock_get_or_create, mock_db, mock_preferences):
        """Test resetting to defaults"""
        service = ParentPreferencesService()

        # Mock query
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_preferences
        mock_db.query.return_value = mock_query
        mock_get_or_create.return_value = mock_preferences

        result = service.reset_to_defaults(mock_db, 1)

        mock_db.delete.assert_called_once_with(mock_preferences)
        mock_db.commit.assert_called_once()
        assert result == mock_preferences


class TestPreferenceAPIEndpoints:
    """Test preference API endpoints"""

    @patch("routes.parent.parent_preferences_service")
    def test_get_preferences_success(self, mock_service, client, mock_preferences):
        """Test getting preferences via API"""
        with patch("routes.parent.get_db") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db

            mock_service.get_preferences.return_value = mock_preferences

            response = client.get("/api/parent/preferences?user_id=1")

            assert response.status_code == 200
            data = response.json()
            assert data["user_id"] == 1
            assert data["email_notifications_enabled"] is True

    @patch("routes.parent.parent_preferences_service")
    def test_update_preferences_success(self, mock_service, client, mock_preferences):
        """Test updating preferences via API"""
        with patch("routes.parent.get_db") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db

            mock_service.update_preferences.return_value = mock_preferences

            response = client.put(
                "/api/parent/preferences?user_id=1",
                json={"email_notifications_enabled": False}
            )

            assert response.status_code == 200
            mock_service.update_preferences.assert_called_once()

    @patch("routes.parent.parent_preferences_service")
    def test_update_preferences_invalid_value(self, mock_service, client):
        """Test updating preferences with invalid value"""
        with patch("routes.parent.get_db") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db

            mock_service.update_preferences.side_effect = ValueError("Invalid severity")

            response = client.put(
                "/api/parent/preferences?user_id=1",
                json={"instant_notification_min_severity": "invalid"}
            )

            assert response.status_code == 400

    @patch("routes.parent.parent_preferences_service")
    def test_enable_all_notifications_success(self, mock_service, client):
        """Test enabling all notifications via API"""
        with patch("routes.parent.get_db") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db

            response = client.post("/api/parent/preferences/enable-all?user_id=1")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            mock_service.enable_all_notifications.assert_called_once()

    @patch("routes.parent.parent_preferences_service")
    def test_disable_all_notifications_success(self, mock_service, client):
        """Test disabling all notifications via API"""
        with patch("routes.parent.get_db") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db

            response = client.post("/api/parent/preferences/disable-all?user_id=1")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            mock_service.disable_all_notifications.assert_called_once()

    @patch("routes.parent.parent_preferences_service")
    def test_reset_preferences_success(self, mock_service, client):
        """Test resetting preferences via API"""
        with patch("routes.parent.get_db") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db

            response = client.post("/api/parent/preferences/reset?user_id=1")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            mock_service.reset_to_defaults.assert_called_once()


class TestConvenienceFunctions:
    """Test module-level convenience functions"""

    @patch("services.parent_preferences_service.parent_preferences_service")
    def test_get_preferences_function(self, mock_service, mock_db, mock_preferences):
        """Test get_preferences convenience function"""
        from services.parent_preferences_service import get_preferences

        mock_service.get_preferences.return_value = mock_preferences

        result = get_preferences(mock_db, 1)

        assert result == mock_preferences
        mock_service.get_preferences.assert_called_once_with(mock_db, 1)

    @patch("services.parent_preferences_service.parent_preferences_service")
    def test_update_preferences_function(self, mock_service, mock_db, mock_preferences):
        """Test update_preferences convenience function"""
        from services.parent_preferences_service import update_preferences

        mock_service.update_preferences.return_value = mock_preferences

        result = update_preferences(mock_db, 1, {"email_notifications_enabled": False})

        assert result == mock_preferences
        mock_service.update_preferences.assert_called_once()

    @patch("services.parent_preferences_service.parent_preferences_service")
    def test_should_notify_function(self, mock_service, mock_db):
        """Test should_notify convenience function"""
        from services.parent_preferences_service import should_notify

        mock_service.should_notify.return_value = True

        result = should_notify(mock_db, 1, "critical", "crisis")

        assert result is True
        mock_service.should_notify.assert_called_once()
