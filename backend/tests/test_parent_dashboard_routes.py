"""
Tests for Parent Dashboard API Routes
Comprehensive test coverage for parent safety monitoring endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from main import app
from models.safety import SafetyFlag
from models.user import User


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Create mock user"""
    user = Mock(spec=User)
    user.id = 1
    user.name = "TestChild"
    user.age = 10
    user.grade = 5
    user.parent_email = "parent@example.com"
    return user


@pytest.fixture
def mock_safety_flag():
    """Create mock safety flag"""
    flag = Mock(spec=SafetyFlag)
    flag.id = 1
    flag.user_id = 1
    flag.message_id = 100
    flag.flag_type = "profanity"
    flag.severity = "medium"
    flag.content_snippet = "Test message content"
    flag.action_taken = "warned"
    flag.timestamp = datetime.now()
    flag.parent_notified = False
    return flag


class TestDashboardOverview:
    """Test parent dashboard overview endpoint"""

    @patch("routes.parent.safety_flag_service")
    def test_get_dashboard_overview_success(self, mock_service, client, mock_user):
        """Test successful dashboard overview retrieval"""
        # Mock database
        with patch("routes.parent.get_db") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db

            # Mock user query
            mock_db.query.return_value.filter.return_value.first.return_value = mock_user

            # Mock service responses
            mock_service.get_user_safety_summary.return_value = {
                "total_flags_all_time": 10,
                "total_flags_last_7_days": 3,
                "critical_flags_count": 1,
                "last_flag_timestamp": datetime.now().isoformat(),
                "most_common_flag_type": "profanity"
            }
            mock_service.get_critical_flags.return_value = []
            mock_service.get_unnotified_flags.return_value = []

            response = client.get("/api/parent/dashboard/overview?user_id=1")

            assert response.status_code == 200
            data = response.json()
            assert data["user_id"] == 1
            assert data["user_name"] == "TestChild"
            assert data["total_flags_all_time"] == 10
            assert data["requires_attention"] is False

    @patch("routes.parent.safety_flag_service")
    def test_get_dashboard_overview_requires_attention(self, mock_service, client, mock_user):
        """Test dashboard overview when attention required"""
        with patch("routes.parent.get_db") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = mock_user

            mock_service.get_user_safety_summary.return_value = {
                "total_flags_all_time": 10,
                "total_flags_last_7_days": 3,
                "critical_flags_count": 2,
                "last_flag_timestamp": datetime.now().isoformat(),
                "most_common_flag_type": "crisis"
            }

            # Return critical unnotified flags
            mock_flag = Mock()
            mock_service.get_critical_flags.return_value = [mock_flag]
            mock_service.get_unnotified_flags.return_value = []

            response = client.get("/api/parent/dashboard/overview?user_id=1")

            assert response.status_code == 200
            data = response.json()
            assert data["requires_attention"] is True
            assert data["critical_flags_count"] == 2

    def test_get_dashboard_overview_user_not_found(self, client):
        """Test dashboard overview with non-existent user"""
        with patch("routes.parent.get_db") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = None

            response = client.get("/api/parent/dashboard/overview?user_id=999")

            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()


class TestGetAllSafetyFlags:
    """Test get all safety flags endpoint"""

    @patch("routes.parent.safety_flag_service")
    def test_get_all_safety_flags_success(self, mock_service, client, mock_safety_flag):
        """Test successful retrieval of all safety flags"""
        with patch("routes.parent.get_db") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db

            mock_service.get_by_user.return_value = [mock_safety_flag]

            response = client.get("/api/parent/safety-flags/all?user_id=1")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["id"] == 1
            assert data[0]["user_id"] == 1
            assert data[0]["flag_type"] == "profanity"

    @patch("routes.parent.safety_flag_service")
    def test_get_all_safety_flags_with_pagination(self, mock_service, client):
        """Test pagination parameters"""
        with patch("routes.parent.get_db") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            mock_service.get_by_user.return_value = []

            response = client.get("/api/parent/safety-flags/all?user_id=1&limit=10&offset=5")

            assert response.status_code == 200
            mock_service.get_by_user.assert_called_once_with(
                mock_db, 1, limit=10, offset=5
            )


class TestGetCriticalSafetyFlags:
    """Test get critical safety flags endpoint"""

    @patch("routes.parent.safety_flag_service")
    def test_get_critical_flags_success(self, mock_service, client, mock_safety_flag):
        """Test retrieval of critical flags"""
        with patch("routes.parent.get_db") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db

            critical_flag = Mock(spec=SafetyFlag)
            critical_flag.id = 2
            critical_flag.user_id = 1
            critical_flag.message_id = 101
            critical_flag.flag_type = "crisis"
            critical_flag.severity = "critical"
            critical_flag.content_snippet = "Crisis content"
            critical_flag.action_taken = "blocked"
            critical_flag.timestamp = datetime.now()
            critical_flag.parent_notified = False

            mock_service.get_critical_flags.return_value = [critical_flag]

            response = client.get("/api/parent/safety-flags/critical?user_id=1")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["severity"] == "critical"
            assert data[0]["flag_type"] == "crisis"

    @patch("routes.parent.safety_flag_service")
    def test_get_critical_flags_with_date_filter(self, mock_service, client):
        """Test critical flags with date filter"""
        with patch("routes.parent.get_db") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            mock_service.get_critical_flags.return_value = []

            response = client.get(
                "/api/parent/safety-flags/critical?user_id=1&since_days=7&include_notified=true"
            )

            assert response.status_code == 200
            # Verify since_date was calculated (approximately 7 days ago)
            call_args = mock_service.get_critical_flags.call_args
            assert call_args[1]["user_id"] == 1
            assert call_args[1]["include_notified"] is True
            assert call_args[1]["since_date"] is not None


class TestGetUnnotifiedSafetyFlags:
    """Test get unnotified safety flags endpoint"""

    @patch("routes.parent.safety_flag_service")
    def test_get_unnotified_flags_success(self, mock_service, client, mock_safety_flag):
        """Test retrieval of unnotified flags"""
        with patch("routes.parent.get_db") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            mock_service.get_unnotified_flags.return_value = [mock_safety_flag]

            response = client.get("/api/parent/safety-flags/unnotified?user_id=1")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["parent_notified"] is False

    @patch("routes.parent.safety_flag_service")
    def test_get_unnotified_flags_with_min_severity(self, mock_service, client):
        """Test unnotified flags with minimum severity filter"""
        with patch("routes.parent.get_db") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            mock_service.get_unnotified_flags.return_value = []

            response = client.get(
                "/api/parent/safety-flags/unnotified?user_id=1&min_severity=high"
            )

            assert response.status_code == 200
            mock_service.get_unnotified_flags.assert_called_once_with(
                mock_db, user_id=1, min_severity="high"
            )

    def test_get_unnotified_flags_invalid_severity(self, client):
        """Test with invalid severity level"""
        with patch("routes.parent.get_db") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db

            response = client.get(
                "/api/parent/safety-flags/unnotified?user_id=1&min_severity=invalid"
            )

            assert response.status_code == 400
            assert "Invalid severity" in response.json()["detail"]


class TestGetSafetyFlagsBySeverity:
    """Test get safety flags by severity endpoint"""

    @patch("routes.parent.safety_flag_service")
    def test_get_flags_by_severity_success(self, mock_service, client, mock_safety_flag):
        """Test retrieval by severity"""
        with patch("routes.parent.get_db") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            mock_service.get_by_severity.return_value = [mock_safety_flag]

            response = client.get("/api/parent/safety-flags/by-severity/medium?user_id=1")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["severity"] == "medium"

    def test_get_flags_by_severity_invalid(self, client):
        """Test with invalid severity level"""
        with patch("routes.parent.get_db") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db

            response = client.get("/api/parent/safety-flags/by-severity/invalid?user_id=1")

            assert response.status_code == 400
            assert "Invalid severity" in response.json()["detail"]


class TestGetSafetyFlagsByType:
    """Test get safety flags by type endpoint"""

    @patch("routes.parent.safety_flag_service")
    def test_get_flags_by_type_success(self, mock_service, client, mock_safety_flag):
        """Test retrieval by type"""
        with patch("routes.parent.get_db") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            mock_service.get_by_type.return_value = [mock_safety_flag]

            response = client.get("/api/parent/safety-flags/by-type/profanity?user_id=1")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["flag_type"] == "profanity"

    def test_get_flags_by_type_invalid(self, client):
        """Test with invalid flag type"""
        with patch("routes.parent.get_db") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db

            response = client.get("/api/parent/safety-flags/by-type/invalid?user_id=1")

            assert response.status_code == 400
            assert "Invalid flag type" in response.json()["detail"]


class TestGetRecentSafetyFlags:
    """Test get recent safety flags endpoint"""

    @patch("routes.parent.safety_flag_service")
    def test_get_recent_flags_success(self, mock_service, client, mock_safety_flag):
        """Test retrieval of recent flags"""
        with patch("routes.parent.get_db") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            mock_service.get_recent_flags.return_value = [mock_safety_flag]

            response = client.get("/api/parent/safety-flags/recent?user_id=1&hours=48")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            mock_service.get_recent_flags.assert_called_once_with(
                mock_db, user_id=1, hours=48
            )


class TestGetSafetyFlagDetail:
    """Test get safety flag detail endpoint"""

    @patch("routes.parent.safety_flag_service")
    def test_get_flag_detail_success(self, mock_service, client, mock_safety_flag):
        """Test retrieval of flag details"""
        with patch("routes.parent.get_db") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            mock_service.get_by_id.return_value = mock_safety_flag

            response = client.get("/api/parent/safety-flags/1?user_id=1")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
            assert data["user_id"] == 1

    @patch("routes.parent.safety_flag_service")
    def test_get_flag_detail_not_found(self, mock_service, client):
        """Test with non-existent flag"""
        with patch("routes.parent.get_db") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            mock_service.get_by_id.return_value = None

            response = client.get("/api/parent/safety-flags/999?user_id=1")

            assert response.status_code == 404

    @patch("routes.parent.safety_flag_service")
    def test_get_flag_detail_wrong_user(self, mock_service, client, mock_safety_flag):
        """Test authorization check - wrong user"""
        with patch("routes.parent.get_db") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db

            # Flag belongs to user 1, but requesting as user 2
            mock_safety_flag.user_id = 1
            mock_service.get_by_id.return_value = mock_safety_flag

            response = client.get("/api/parent/safety-flags/1?user_id=2")

            assert response.status_code == 403
            assert "Not authorized" in response.json()["detail"]


class TestGetSafetyStatistics:
    """Test get safety statistics endpoint"""

    @patch("routes.parent.safety_flag_service")
    def test_get_statistics_success(self, mock_service, client):
        """Test retrieval of statistics"""
        with patch("routes.parent.get_db") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db

            mock_service.get_stats.return_value = {
                "total_flags": 15,
                "by_severity": {"low": 5, "medium": 7, "high": 2, "critical": 1},
                "by_type": {"profanity": 10, "bullying": 3, "crisis": 2},
                "parent_notified": 10,
                "parent_unnotified": 5,
                "last_24_hours": 3
            }

            response = client.get("/api/parent/statistics?user_id=1")

            assert response.status_code == 200
            data = response.json()
            assert data["total_flags"] == 15
            assert data["by_severity"]["critical"] == 1
            assert data["by_type"]["profanity"] == 10

    @patch("routes.parent.safety_flag_service")
    def test_get_statistics_with_date_filter(self, mock_service, client):
        """Test statistics with date filter"""
        with patch("routes.parent.get_db") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            mock_service.get_stats.return_value = {
                "total_flags": 5,
                "by_severity": {"low": 2, "medium": 2, "high": 1, "critical": 0},
                "by_type": {"profanity": 3, "bullying": 2},
                "parent_notified": 3,
                "parent_unnotified": 2,
                "last_24_hours": 1
            }

            response = client.get("/api/parent/statistics?user_id=1&since_days=7")

            assert response.status_code == 200
            call_args = mock_service.get_stats.call_args
            assert call_args[1]["user_id"] == 1
            assert call_args[1]["since_date"] is not None


class TestGetNotificationHistory:
    """Test get notification history endpoint"""

    @patch("routes.parent.parent_notification_service")
    def test_get_notification_history_success(self, mock_service, client):
        """Test retrieval of notification history"""
        with patch("routes.parent.get_db") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db

            mock_service.get_notification_history.return_value = [
                {
                    "timestamp": datetime.now().isoformat(),
                    "severity": "critical",
                    "flag_type": "crisis",
                    "content_snippet": "Crisis content",
                    "action_taken": "blocked"
                }
            ]

            response = client.get("/api/parent/notifications/history?user_id=1&limit=10")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["severity"] == "critical"


class TestAcknowledgeSafetyFlag:
    """Test acknowledge safety flag endpoint"""

    @patch("routes.parent.safety_flag_service")
    def test_acknowledge_flag_success(self, mock_service, client, mock_safety_flag):
        """Test successful flag acknowledgment"""
        with patch("routes.parent.get_db") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db

            mock_service.get_by_id.return_value = mock_safety_flag
            mock_service.mark_parent_notified.return_value = True

            response = client.post("/api/parent/safety-flags/1/acknowledge?user_id=1")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["flag_id"] == 1

    @patch("routes.parent.safety_flag_service")
    def test_acknowledge_flag_not_found(self, mock_service, client):
        """Test acknowledgment of non-existent flag"""
        with patch("routes.parent.get_db") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            mock_service.get_by_id.return_value = None

            response = client.post("/api/parent/safety-flags/999/acknowledge?user_id=1")

            assert response.status_code == 404

    @patch("routes.parent.safety_flag_service")
    def test_acknowledge_flag_wrong_user(self, mock_service, client, mock_safety_flag):
        """Test authorization check for acknowledgment"""
        with patch("routes.parent.get_db") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db

            mock_safety_flag.user_id = 1
            mock_service.get_by_id.return_value = mock_safety_flag

            response = client.post("/api/parent/safety-flags/1/acknowledge?user_id=2")

            assert response.status_code == 403


class TestAcknowledgeMultipleFlags:
    """Test acknowledge multiple flags endpoint"""

    @patch("routes.parent.safety_flag_service")
    def test_acknowledge_multiple_success(self, mock_service, client):
        """Test successful multiple flag acknowledgment"""
        with patch("routes.parent.get_db") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db

            # Mock flags
            flag1 = Mock(spec=SafetyFlag)
            flag1.id = 1
            flag1.user_id = 1

            flag2 = Mock(spec=SafetyFlag)
            flag2.id = 2
            flag2.user_id = 1

            def get_flag_by_id(db, flag_id):
                if flag_id == 1:
                    return flag1
                elif flag_id == 2:
                    return flag2
                return None

            mock_service.get_by_id.side_effect = get_flag_by_id
            mock_service.mark_multiple_parent_notified.return_value = 2

            response = client.post(
                "/api/parent/safety-flags/acknowledge-multiple?user_id=1",
                json=[1, 2]
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["count"] == 2

    @patch("routes.parent.safety_flag_service")
    def test_acknowledge_multiple_empty_list(self, mock_service, client):
        """Test with empty flag list"""
        with patch("routes.parent.get_db") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db

            response = client.post(
                "/api/parent/safety-flags/acknowledge-multiple?user_id=1",
                json=[]
            )

            assert response.status_code == 400
            assert "No flag IDs provided" in response.json()["detail"]

    @patch("routes.parent.safety_flag_service")
    def test_acknowledge_multiple_wrong_user(self, mock_service, client):
        """Test authorization check for multiple flags"""
        with patch("routes.parent.get_db") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db

            flag = Mock(spec=SafetyFlag)
            flag.id = 1
            flag.user_id = 2  # Different user

            mock_service.get_by_id.return_value = flag

            response = client.post(
                "/api/parent/safety-flags/acknowledge-multiple?user_id=1",
                json=[1]
            )

            assert response.status_code == 403
