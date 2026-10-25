"""
Shared pytest configuration

Points the application database at a temporary SQLite file for the whole test session,
so tests that use database.database.SessionLocal never write to the real data/chatbot.db.
This must run before any application module is imported, which is why it lives at module level.
"""

import os
import tempfile

_test_db_dir = tempfile.mkdtemp(prefix="chatbot-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_test_db_dir, 'test.db')}"
# The test client's requests are for host "testserver"
os.environ["ALLOWED_HOSTS"] = '["127.0.0.1", "localhost", "testserver"]'


import inspect

import pytest


@pytest.fixture
def client():
    """
    FastAPI test client for route tests

    - Authentication is satisfied by an override, so route logic can be tested without a token.
    - The database dependency resolves routes.parent.get_db at request time, so tests can
      substitute a mock session with patch("routes.parent.get_db").
    """
    from fastapi.testclient import TestClient

    import routes.parent
    from database.database import get_db
    from main import app
    from utils.auth_dependencies import get_current_user, require_parent_auth

    def _get_db_override():
        result = routes.parent.get_db()
        if inspect.isgenerator(result):
            yield from result
        else:
            yield result

    app.dependency_overrides[get_db] = _get_db_override
    app.dependency_overrides[get_current_user] = lambda: {"sub": "parent", "access": "test"}
    app.dependency_overrides[require_parent_auth] = lambda: {"sub": "parent", "access": "test"}
    yield TestClient(app)
    app.dependency_overrides.clear()
