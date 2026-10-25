"""
Protections of the local API and the parent account: the per-launch API token, the
allowed host names, JWT secrets and tokens after a password change, and parent emails.
"""

import ssl
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app
from services.auth_service import AuthService
from services.email_service import EmailService


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_api_token_is_required_when_set(client):
    with patch("main.settings.API_TOKEN", "secret-token"):
        assert client.get("/api/cache/stats").status_code == 401
        assert client.get("/api/cache/stats", headers={"X-API-Token": "wrong"}).status_code == 401
        assert client.get("/api/cache/stats", headers={"X-API-Token": "secret-token"}).status_code == 200
        # The health check and CORS preflight requests need no token
        assert client.get("/health").status_code == 200
        preflight = client.options("/api/message", headers={
            "Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"})
        assert preflight.status_code == 200


def test_no_api_token_needed_when_unset(client):
    with patch("main.settings.API_TOKEN", None):
        assert client.get("/api/cache/stats").status_code == 200


def test_other_host_names_are_refused(client):
    # A web page that pointed its own domain at 127.0.0.1 (DNS rebinding)
    assert client.get("/api/cache/stats", headers={"Host": "evil.example.com"}).status_code == 400
    assert client.get("/api/cache/stats", headers={"Host": "localhost:8000"}).status_code == 200


def test_setup_password_does_not_return_an_existing_jwt_secret(client):
    with patch("routes.parent.settings") as settings:
        settings.PARENT_DASHBOARD_PASSWORD = None
        settings.JWT_SECRET_KEY = "existing-secret"
        response = client.post("/api/parent/auth/setup-password", json={"password": "Blue-Kite-Garden-42"})
    assert response.status_code == 200
    assert "existing-secret" not in response.text and "jwt_secret" not in response.json()


def test_setup_password_generates_a_secret_when_none_is_set(client):
    with patch("routes.parent.settings") as settings:
        settings.PARENT_DASHBOARD_PASSWORD = None
        settings.JWT_SECRET_KEY = None
        response = client.post("/api/parent/auth/setup-password", json={"password": "Blue-Kite-Garden-42"})
    assert response.status_code == 200 and len(response.json()["jwt_secret"]) >= 32


def test_tokens_end_when_the_password_changes():
    service = AuthService()
    service.secret_key = "test-secret"
    with patch("services.auth_service.settings.PARENT_DASHBOARD_PASSWORD", "hash-one"):
        token = service.create_access_token({"sub": "parent"})
        assert service.verify_token(token) is not None
    with patch("services.auth_service.settings.PARENT_DASHBOARD_PASSWORD", "hash-two"):
        assert service.verify_token(token) is None


def _email_service(use_tls=True):
    with patch("services.email_service.settings") as settings:
        settings.SMTP_HOST, settings.SMTP_PORT = "smtp.test.com", 587
        settings.SMTP_USERNAME, settings.SMTP_PASSWORD = "user@test.com", "password"
        settings.SMTP_FROM_EMAIL = "from@test.com"
        settings.SMTP_USE_TLS = use_tls
        settings.ENABLE_PARENT_NOTIFICATIONS = True
        return EmailService()


@patch("smtplib.SMTP")
def test_smtp_certificate_is_checked(mock_smtp):
    server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = server
    assert _email_service().send_email("parent@example.com", "Subject", "Body")["success"] is True
    context = server.starttls.call_args.kwargs["context"]
    assert isinstance(context, ssl.SSLContext) and context.verify_mode == ssl.CERT_REQUIRED


@patch("smtplib.SMTP")
def test_password_is_not_sent_without_tls(mock_smtp):
    result = _email_service(use_tls=False).send_email("parent@example.com", "Subject", "Body")
    assert result["success"] is False
    mock_smtp.assert_not_called()


@patch("smtplib.SMTP")
def test_line_break_in_subject_does_not_add_a_header(mock_smtp):
    server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = server
    _email_service().send_email("parent@example.com", "Alert for Lily\r\nBcc: someone@evil.com", "Body")
    message = server.send_message.call_args.args[0]
    assert message["Bcc"] is None and message["Subject"] == "Alert for Lily Bcc: someone@evil.com"


def test_childs_name_is_escaped_in_html_emails():
    service = _email_service()
    name = '<a href="https://evil.example.com">Lily</a>'
    from datetime import datetime
    alert = service._generate_html_alert(name, "crisis_suicide", "critical", {}, datetime.now())
    summary = service._generate_html_summary(name, [{"severity": "high", "flag_type": "bullying"}], "weekly")
    for html in (alert, summary):
        assert "<a href" not in html and "&lt;a href=" in html
