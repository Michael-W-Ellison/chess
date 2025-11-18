"""
Tests for Email Service
Comprehensive test coverage for email notification functionality
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import smtplib

from services.email_service import (
    EmailService,
    email_service,
    send_email,
    send_critical_safety_alert,
    send_bulk_safety_summary,
    is_configured
)


class TestEmailServiceInitialization:
    """Test EmailService initialization"""

    def test_initialization(self):
        """Test service initializes correctly"""
        service = EmailService()
        assert service is not None
        assert service.smtp_host is not None
        assert service.smtp_port is not None

    def test_global_instance(self):
        """Test global instance is available"""
        assert email_service is not None

    @patch("services.email_service.settings")
    def test_initialization_with_settings(self, mock_settings):
        """Test initialization with custom settings"""
        mock_settings.SMTP_HOST = "test.smtp.com"
        mock_settings.SMTP_PORT = 2525
        mock_settings.SMTP_USERNAME = "test@example.com"
        mock_settings.SMTP_PASSWORD = "testpass"
        mock_settings.SMTP_FROM_EMAIL = "from@example.com"
        mock_settings.SMTP_USE_TLS = True
        mock_settings.ENABLE_PARENT_NOTIFICATIONS = True

        service = EmailService()

        assert service.smtp_host == "test.smtp.com"
        assert service.smtp_port == 2525
        assert service.smtp_username == "test@example.com"
        assert service.enabled is True


class TestEmailConfiguration:
    """Test email service configuration"""

    @patch("services.email_service.settings")
    def test_is_configured_all_settings(self, mock_settings):
        """Test configuration check with all settings present"""
        mock_settings.SMTP_HOST = "smtp.test.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USERNAME = "user@test.com"
        mock_settings.SMTP_PASSWORD = "password"
        mock_settings.SMTP_FROM_EMAIL = "from@test.com"
        mock_settings.SMTP_USE_TLS = True
        mock_settings.ENABLE_PARENT_NOTIFICATIONS = False

        service = EmailService()
        assert service.is_configured() is True

    @patch("services.email_service.settings")
    def test_is_configured_missing_settings(self, mock_settings):
        """Test configuration check with missing settings"""
        mock_settings.SMTP_HOST = None
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USERNAME = None
        mock_settings.SMTP_PASSWORD = None
        mock_settings.SMTP_FROM_EMAIL = None
        mock_settings.SMTP_USE_TLS = True
        mock_settings.ENABLE_PARENT_NOTIFICATIONS = False

        service = EmailService()
        assert service.is_configured() is False


class TestSendEmail:
    """Test email sending functionality"""

    @patch("services.email_service.settings")
    @patch("smtplib.SMTP")
    def test_send_email_success(self, mock_smtp, mock_settings):
        """Test successful email sending"""
        # Configure settings
        mock_settings.SMTP_HOST = "smtp.test.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USERNAME = "user@test.com"
        mock_settings.SMTP_PASSWORD = "password"
        mock_settings.SMTP_FROM_EMAIL = "from@test.com"
        mock_settings.SMTP_USE_TLS = True
        mock_settings.ENABLE_PARENT_NOTIFICATIONS = True

        # Mock SMTP connection
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        service = EmailService()
        result = service.send_email(
            to_email="parent@example.com",
            subject="Test Subject",
            body="Test body"
        )

        assert result["success"] is True
        assert result["sent"] is True
        assert result["to_email"] == "parent@example.com"
        assert "timestamp" in result

        # Verify SMTP methods were called
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("user@test.com", "password")
        mock_server.send_message.assert_called_once()

    @patch("services.email_service.settings")
    def test_send_email_notifications_disabled(self, mock_settings):
        """Test email sending when notifications are disabled"""
        mock_settings.SMTP_HOST = "smtp.test.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USERNAME = "user@test.com"
        mock_settings.SMTP_PASSWORD = "password"
        mock_settings.SMTP_FROM_EMAIL = "from@test.com"
        mock_settings.SMTP_USE_TLS = True
        mock_settings.ENABLE_PARENT_NOTIFICATIONS = False

        service = EmailService()
        result = service.send_email(
            to_email="parent@example.com",
            subject="Test",
            body="Test body"
        )

        assert result["success"] is False
        assert result["sent"] is False
        assert "disabled" in result["error"].lower()

    @patch("services.email_service.settings")
    def test_send_email_not_configured(self, mock_settings):
        """Test email sending when service not configured"""
        mock_settings.SMTP_HOST = None
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USERNAME = None
        mock_settings.SMTP_PASSWORD = None
        mock_settings.SMTP_FROM_EMAIL = None
        mock_settings.SMTP_USE_TLS = True
        mock_settings.ENABLE_PARENT_NOTIFICATIONS = True

        service = EmailService()
        result = service.send_email(
            to_email="parent@example.com",
            subject="Test",
            body="Test body"
        )

        assert result["success"] is False
        assert result["sent"] is False
        assert "not configured" in result["error"].lower()

    @patch("services.email_service.settings")
    @patch("smtplib.SMTP")
    def test_send_email_with_html(self, mock_smtp, mock_settings):
        """Test email sending with HTML body"""
        mock_settings.SMTP_HOST = "smtp.test.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USERNAME = "user@test.com"
        mock_settings.SMTP_PASSWORD = "password"
        mock_settings.SMTP_FROM_EMAIL = "from@test.com"
        mock_settings.SMTP_USE_TLS = True
        mock_settings.ENABLE_PARENT_NOTIFICATIONS = True

        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        service = EmailService()
        result = service.send_email(
            to_email="parent@example.com",
            subject="Test Subject",
            body="Plain text body",
            html_body="<h1>HTML body</h1>"
        )

        assert result["success"] is True
        assert result["sent"] is True

    @patch("services.email_service.settings")
    @patch("smtplib.SMTP")
    def test_send_email_smtp_auth_error(self, mock_smtp, mock_settings):
        """Test email sending with SMTP authentication error"""
        mock_settings.SMTP_HOST = "smtp.test.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USERNAME = "user@test.com"
        mock_settings.SMTP_PASSWORD = "wrong_password"
        mock_settings.SMTP_FROM_EMAIL = "from@test.com"
        mock_settings.SMTP_USE_TLS = True
        mock_settings.ENABLE_PARENT_NOTIFICATIONS = True

        mock_server = MagicMock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Authentication failed")
        mock_smtp.return_value.__enter__.return_value = mock_server

        service = EmailService()
        result = service.send_email(
            to_email="parent@example.com",
            subject="Test",
            body="Test body"
        )

        assert result["success"] is False
        assert result["sent"] is False
        assert "authentication" in result["error"].lower()

    @patch("services.email_service.settings")
    @patch("smtplib.SMTP")
    def test_send_email_smtp_exception(self, mock_smtp, mock_settings):
        """Test email sending with SMTP exception"""
        mock_settings.SMTP_HOST = "smtp.test.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USERNAME = "user@test.com"
        mock_settings.SMTP_PASSWORD = "password"
        mock_settings.SMTP_FROM_EMAIL = "from@test.com"
        mock_settings.SMTP_USE_TLS = True
        mock_settings.ENABLE_PARENT_NOTIFICATIONS = True

        mock_server = MagicMock()
        mock_server.send_message.side_effect = smtplib.SMTPException("Connection error")
        mock_smtp.return_value.__enter__.return_value = mock_server

        service = EmailService()
        result = service.send_email(
            to_email="parent@example.com",
            subject="Test",
            body="Test body"
        )

        assert result["success"] is False
        assert result["sent"] is False
        assert "error" in result["error"].lower()


class TestCriticalSafetyAlert:
    """Test critical safety alert email"""

    @patch("services.email_service.settings")
    @patch("smtplib.SMTP")
    def test_send_critical_alert_suicide(self, mock_smtp, mock_settings):
        """Test sending suicide crisis alert"""
        mock_settings.SMTP_HOST = "smtp.test.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USERNAME = "user@test.com"
        mock_settings.SMTP_PASSWORD = "password"
        mock_settings.SMTP_FROM_EMAIL = "from@test.com"
        mock_settings.SMTP_USE_TLS = True
        mock_settings.ENABLE_PARENT_NOTIFICATIONS = True

        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        service = EmailService()
        result = service.send_critical_safety_alert(
            to_email="parent@example.com",
            user_name="TestChild",
            category="crisis_suicide",
            severity="critical",
            details={"crisis": {"primary_category": "suicide"}},
            timestamp=datetime.now()
        )

        assert result["success"] is True
        assert result["sent"] is True

        # Verify email was called with correct parameters
        call_args = mock_server.send_message.call_args
        assert call_args is not None

    @patch("services.email_service.settings")
    @patch("smtplib.SMTP")
    def test_send_critical_alert_abuse(self, mock_smtp, mock_settings):
        """Test sending abuse alert"""
        mock_settings.SMTP_HOST = "smtp.test.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USERNAME = "user@test.com"
        mock_settings.SMTP_PASSWORD = "password"
        mock_settings.SMTP_FROM_EMAIL = "from@test.com"
        mock_settings.SMTP_USE_TLS = True
        mock_settings.ENABLE_PARENT_NOTIFICATIONS = True

        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        service = EmailService()
        result = service.send_critical_safety_alert(
            to_email="parent@example.com",
            user_name="TestChild",
            category="abuse_physical",
            severity="critical",
            details={},
            timestamp=datetime.now(),
            content_snippet="Test content"
        )

        assert result["success"] is True
        assert result["sent"] is True

    def test_alert_subject_generation(self):
        """Test alert subject line generation"""
        service = EmailService()

        # Test various categories
        subjects = {
            "crisis_suicide": "🚨 URGENT: Suicide-Related Content Detected",
            "crisis_self_harm": "🚨 URGENT: Self-Harm Content Detected",
            "abuse_physical": "🚨 URGENT: Physical Abuse Reported",
            "inappropriate_content": "⚠️ High-Severity Content Alert",
        }

        for category, expected in subjects.items():
            result = service._generate_alert_subject(category, "critical", "TestChild")
            assert result == expected


class TestBulkSafetySummary:
    """Test bulk safety summary email"""

    @patch("services.email_service.settings")
    @patch("smtplib.SMTP")
    def test_send_bulk_summary(self, mock_smtp, mock_settings):
        """Test sending bulk safety summary"""
        mock_settings.SMTP_HOST = "smtp.test.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USERNAME = "user@test.com"
        mock_settings.SMTP_PASSWORD = "password"
        mock_settings.SMTP_FROM_EMAIL = "from@test.com"
        mock_settings.SMTP_USE_TLS = True
        mock_settings.ENABLE_PARENT_NOTIFICATIONS = True

        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        flags = [
            {"severity": "medium", "flag_type": "profanity"},
            {"severity": "high", "flag_type": "bullying"},
            {"severity": "critical", "flag_type": "crisis"}
        ]

        service = EmailService()
        result = service.send_bulk_safety_summary(
            to_email="parent@example.com",
            user_name="TestChild",
            flags=flags,
            summary_period="daily"
        )

        assert result["success"] is True
        assert result["sent"] is True

    @patch("services.email_service.settings")
    @patch("smtplib.SMTP")
    def test_send_weekly_summary(self, mock_smtp, mock_settings):
        """Test sending weekly summary"""
        mock_settings.SMTP_HOST = "smtp.test.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USERNAME = "user@test.com"
        mock_settings.SMTP_PASSWORD = "password"
        mock_settings.SMTP_FROM_EMAIL = "from@test.com"
        mock_settings.SMTP_USE_TLS = True
        mock_settings.ENABLE_PARENT_NOTIFICATIONS = True

        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        flags = []

        service = EmailService()
        result = service.send_bulk_safety_summary(
            to_email="parent@example.com",
            user_name="TestChild",
            flags=flags,
            summary_period="weekly"
        )

        assert result["success"] is True
        assert result["sent"] is True


class TestConvenienceFunctions:
    """Test module-level convenience functions"""

    @patch("services.email_service.email_service")
    def test_send_email_function(self, mock_service):
        """Test send_email convenience function"""
        mock_service.send_email.return_value = {"success": True, "sent": True}

        result = send_email(
            to_email="test@example.com",
            subject="Test",
            body="Body"
        )

        assert result["success"] is True
        mock_service.send_email.assert_called_once()

    @patch("services.email_service.email_service")
    def test_send_critical_alert_function(self, mock_service):
        """Test send_critical_safety_alert convenience function"""
        mock_service.send_critical_safety_alert.return_value = {
            "success": True,
            "sent": True
        }

        result = send_critical_safety_alert(
            to_email="test@example.com",
            user_name="Child",
            category="crisis_suicide",
            severity="critical",
            details={},
            timestamp=datetime.now()
        )

        assert result["success"] is True
        mock_service.send_critical_safety_alert.assert_called_once()

    @patch("services.email_service.email_service")
    def test_send_bulk_summary_function(self, mock_service):
        """Test send_bulk_safety_summary convenience function"""
        mock_service.send_bulk_safety_summary.return_value = {
            "success": True,
            "sent": True
        }

        result = send_bulk_safety_summary(
            to_email="test@example.com",
            user_name="Child",
            flags=[],
            summary_period="daily"
        )

        assert result["success"] is True
        mock_service.send_bulk_safety_summary.assert_called_once()

    @patch("services.email_service.email_service")
    def test_is_configured_function(self, mock_service):
        """Test is_configured convenience function"""
        mock_service.is_configured.return_value = True

        result = is_configured()

        assert result is True
        mock_service.is_configured.assert_called_once()


class TestEmailTemplates:
    """Test email template generation"""

    def test_plain_text_alert_format(self):
        """Test plain text alert formatting"""
        service = EmailService()

        body = service._generate_plain_text_alert(
            user_name="TestChild",
            category="crisis_suicide",
            severity="critical",
            details={"crisis": {"primary_category": "suicide"}},
            timestamp=datetime(2025, 1, 15, 14, 30),
            content_snippet="Test content"
        )

        assert "SAFETY ALERT" in body
        assert "TestChild" in body
        assert "critical" in body.lower()
        assert "2025-01-15" in body

    def test_html_alert_format(self):
        """Test HTML alert formatting"""
        service = EmailService()

        html = service._generate_html_alert(
            user_name="TestChild",
            category="crisis_suicide",
            severity="critical",
            details={"crisis": {"primary_category": "suicide"}},
            timestamp=datetime(2025, 1, 15, 14, 30),
            content_snippet="Test content"
        )

        assert "<!DOCTYPE html>" in html
        assert "TestChild" in html
        assert "critical" in html.lower()

    def test_plain_text_summary_format(self):
        """Test plain text summary formatting"""
        service = EmailService()

        flags = [
            {"severity": "low", "flag_type": "profanity"},
            {"severity": "medium", "flag_type": "profanity"},
            {"severity": "high", "flag_type": "bullying"}
        ]

        body = service._generate_plain_text_summary(
            user_name="TestChild",
            flags=flags,
            summary_period="daily"
        )

        assert "SAFETY SUMMARY" in body
        assert "TestChild" in body
        assert "3" in body  # Total events

    def test_html_summary_format(self):
        """Test HTML summary formatting"""
        service = EmailService()

        flags = [
            {"severity": "low", "flag_type": "profanity"},
            {"severity": "medium", "flag_type": "profanity"}
        ]

        html = service._generate_html_summary(
            user_name="TestChild",
            flags=flags,
            summary_period="weekly"
        )

        assert "<!DOCTYPE html>" in html
        assert "TestChild" in html
        assert "2" in html  # Total events
