"""
Tests for the router-level authentication guard on the parent API
Every /api/parent endpoint except /auth/* must require a token when password protection is on.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from main import app


PROTECTED_REQUESTS = [
    ("get", "/api/parent/safety-flags/all?user_id=1"),
    ("get", "/api/parent/safety-flags/stats?user_id=1"),
    ("get", "/api/parent/preferences?user_id=1"),
    ("put", "/api/parent/preferences?user_id=1"),
    ("post", "/api/parent/preferences/disable-all?user_id=1"),
    ("post", "/api/parent/safety-flags/1/acknowledge?user_id=1"),
    ("get", "/api/parent/conversations?user_id=1"),
    ("get", "/api/parent/reports/preview?user_id=1"),
    ("get", "/api/parent/engagement?user_id=1"),
    ("get", "/api/parent/language-model"),
    ("put", "/api/parent/language-model"),
]


@pytest.fixture
def unauthenticated_client():
    """Test client with password protection required and configured, and no overrides"""
    app.dependency_overrides.clear()
    with patch("utils.auth_dependencies.settings") as mock_settings, \
            patch("utils.auth_dependencies.auth_service") as mock_auth:
        mock_settings.PARENT_DASHBOARD_REQUIRE_PASSWORD = True
        mock_auth.is_configured = True
        mock_auth.verify_token.return_value = None
        yield TestClient(app)


@pytest.mark.parametrize("method,url", PROTECTED_REQUESTS)
def test_parent_endpoints_require_token(unauthenticated_client, method, url):
    response = getattr(unauthenticated_client, method)(url)
    assert response.status_code == 401


@pytest.mark.parametrize("method,url", PROTECTED_REQUESTS)
def test_parent_endpoints_reject_invalid_token(unauthenticated_client, method, url):
    response = getattr(unauthenticated_client, method)(
        url, headers={"Authorization": "Bearer not-a-valid-token"}
    )
    assert response.status_code == 401


def test_auth_status_is_public(unauthenticated_client):
    response = unauthenticated_client.get("/api/parent/auth/status")
    assert response.status_code == 200


def test_auth_requirements_is_public(unauthenticated_client):
    response = unauthenticated_client.get("/api/parent/auth/requirements")
    assert response.status_code == 200


def test_valid_token_is_accepted(unauthenticated_client):
    with patch("utils.auth_dependencies.auth_service") as mock_auth, \
            patch("routes.parent.safety_flag_service") as mock_service:
        mock_auth.is_configured = True
        mock_auth.verify_token.return_value = {"sub": "parent"}
        mock_service.get_stats.return_value = {}

        response = unauthenticated_client.get(
            "/api/parent/safety-flags/stats?user_id=1",
            headers={"Authorization": "Bearer valid-token"},
        )

    assert response.status_code != 401


@pytest.fixture
def unconfigured_client():
    """Test client with password protection required but no password set up"""
    app.dependency_overrides.clear()
    with patch("utils.auth_dependencies.settings") as mock_settings, \
            patch("utils.auth_dependencies.auth_service") as mock_auth:
        mock_settings.PARENT_DASHBOARD_REQUIRE_PASSWORD = True
        mock_auth.is_configured = False
        yield TestClient(app)


@pytest.mark.parametrize("method,url", PROTECTED_REQUESTS)
def test_unconfigured_password_returns_503(unconfigured_client, method, url):
    response = getattr(unconfigured_client, method)(url, headers={"Authorization": "Bearer any-token"})
    assert response.status_code == 503
    assert "PARENT_DASHBOARD_PASSWORD" in response.json()["detail"]


def test_unconfigured_dashboard_returns_503(unconfigured_client):
    # /dashboard also declares RequireAuth as a parameter
    assert unconfigured_client.get("/api/parent/dashboard?user_id=1").status_code == 503


def test_auth_status_reports_unconfigured(unconfigured_client):
    response = unconfigured_client.get("/api/parent/auth/status")
    assert response.status_code == 200
