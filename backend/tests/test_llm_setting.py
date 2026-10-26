"""
The language model is off by default; a parent turns it on from the dashboard only after
accepting a warning that its replies might exceed the safety mechanisms.
"""

import importlib
from unittest.mock import patch

import pytest

from database.database import Base, SessionLocal, engine
from services.llm_setting import LLM_WARNING, llm_setting
from utils.config import Settings


@pytest.fixture(autouse=True)
def fresh_setting():
    """Each test starts with no stored choice, and leaves none behind"""
    import models  # noqa: F401  (registers the tables)
    from models.app_setting import AppSetting

    Base.metadata.create_all(engine)

    def clear():
        db = SessionLocal()
        db.query(AppSetting).delete()
        db.commit()
        db.close()
        llm_setting._enabled = None

    clear()
    yield
    clear()


def test_off_by_default():
    assert Settings(_env_file=None).USE_LLM is False
    assert llm_setting.enabled() is False


def test_turning_on_requires_accepting_the_warning():
    db = SessionLocal()
    try:
        with pytest.raises(ValueError):
            llm_setting.set_enabled(db, True)
        assert llm_setting.enabled() is False
        llm_setting.set_enabled(db, True, warning_accepted=True)
        assert llm_setting.enabled() is True
        assert llm_setting.status(db)["warning_accepted_at"]
    finally:
        db.close()


def test_choice_is_stored():
    db = SessionLocal()
    try:
        llm_setting.set_enabled(db, True, warning_accepted=True)
    finally:
        db.close()
    llm_setting._enabled = None  # as after a restart
    assert llm_setting.enabled() is True


def test_warning_says_replies_might_exceed_the_safety_mechanisms():
    assert "might exceed the app's safety mechanisms" in LLM_WARNING


def test_route_refuses_to_turn_on_without_the_warning(client):
    status = client.get("/api/parent/language-model").json()
    assert status["enabled"] is False and status["warning"] == LLM_WARNING
    response = client.put("/api/parent/language-model", json={"enabled": True})
    assert response.status_code == 400
    assert client.get("/api/parent/language-model").json()["enabled"] is False


def test_route_turns_on_and_off(client):
    llm_service = importlib.import_module("services.llm_service").llm_service
    with patch.object(llm_service, "load_model") as load, patch.object(llm_service, "unload_model") as unload:
        on = client.put("/api/parent/language-model", json={"enabled": True, "warning_accepted": True})
        assert on.status_code == 200 and on.json()["enabled"] is True
        off = client.put("/api/parent/language-model", json={"enabled": False})
        assert off.status_code == 200 and off.json()["enabled"] is False
    unload.assert_called_once()
    # A model is loaded only when a file is present
    assert load.call_count == (1 if on.json()["model_available"] else 0)


def test_replies_do_not_use_the_model_when_off(client):
    cm = importlib.import_module("services.conversation_manager")
    start = client.post("/api/conversation/start?user_id=7406").json()
    with patch.object(cm.llm_service, "ensure_loaded", return_value=True) as ensure, \
            patch.object(cm.llm_service, "generate", return_value="MODEL REPLY") as generate:
        reply = client.post("/api/message", json={
            "content": "I like dogs", "conversation_id": start["conversation_id"], "user_id": 7406}).json()
    ensure.assert_not_called()
    generate.assert_not_called()
    assert reply["content"] != "MODEL REPLY"


def test_replies_use_the_model_when_a_parent_turned_it_on(client):
    cm = importlib.import_module("services.conversation_manager")
    db = SessionLocal()
    try:
        llm_setting.set_enabled(db, True, warning_accepted=True)
    finally:
        db.close()
    start = client.post("/api/conversation/start?user_id=7407").json()
    with patch.object(cm.llm_service, "ensure_loaded", return_value=True), \
            patch.object(cm.llm_service, "generate", return_value="Dogs are great friends!") as generate:
        client.post("/api/message", json={
            "content": "I like dogs", "conversation_id": start["conversation_id"], "user_id": 7407})
    assert generate.called
