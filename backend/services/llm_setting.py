"""
Whether the language model writes replies.

The app runs without a language model by default: replies, memory extraction and
conversation summaries come from the rule-based engine, whose replies are written by hand.
A parent can turn the model on from the parent dashboard, after confirming they read
LLM_WARNING. USE_LLM=true in .env turns it on for every launch, but it too takes effect only
once the warning has been accepted in the dashboard: until then the model stays off.
Turning the model off in the dashboard withdraws the acceptance, so the model goes off
whether or not USE_LLM is set.

The parent's choice and the acceptance are stored in the app_settings table and kept in
memory here, so the check made for every message does not query the database.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from sqlalchemy.orm import Session

from models.app_setting import AppSetting
from utils.config import settings

logger = logging.getLogger("chatbot.llm_setting")

ENABLED_KEY = "llm_enabled"
ACCEPTED_AT_KEY = "llm_warning_accepted_at"

LLM_WARNING = (
    "A language model writes its own replies instead of choosing from replies written in advance. "
    "Its replies are checked for some kinds of unsafe advice (violence, weapons, dangerous "
    "activities, keeping secrets from parents, sharing personal information), and a reply caught "
    "by these checks is replaced with a rule-based one. These checks look for specific words and "
    "phrases. They will not catch every unsafe, inaccurate or inappropriate reply, so the model's "
    "replies might exceed the app's safety mechanisms. The model can also state things that are "
    "false. The child's own messages are checked by the safety filter as before, with or without "
    "the model."
)


class LLMSetting:
    """The stored on/off choice, read once from the database and updated when it changes"""

    def __init__(self):
        self._enabled: Optional[bool] = None
        self._accepted: Optional[bool] = None

    def load(self, db: Session) -> bool:
        """Read the stored choice (off when none is stored) and whether the warning is accepted"""
        row = db.get(AppSetting, ENABLED_KEY)
        self._enabled = bool(row and row.value == "true")
        self._accepted = db.get(AppSetting, ACCEPTED_AT_KEY) is not None
        return self._enabled

    def _ensure_loaded(self) -> bool:
        """Load the stored values if not yet loaded; False if they could not be read"""
        if self._enabled is not None and self._accepted is not None:
            return True
        from database.database import SessionLocal

        db = SessionLocal()
        try:
            self.load(db)
            return True
        except Exception as e:
            logger.error(f"Could not read the language model setting: {e}")
            return False
        finally:
            db.close()

    def stored_enabled(self) -> bool:
        """The parent's choice, as last loaded or set (off when it cannot be read)"""
        return self._ensure_loaded() and bool(self._enabled)

    def warning_accepted(self) -> bool:
        """Whether a parent accepted LLM_WARNING (and has not turned the model off since)"""
        return self._ensure_loaded() and bool(self._accepted)

    def enabled(self) -> bool:
        """
        Whether replies may come from the language model: turned on (by the parent or USE_LLM)
        and the warning accepted
        """
        return (settings.USE_LLM or self.stored_enabled()) and self.warning_accepted()

    def set_enabled(self, db: Session, enabled: bool, warning_accepted: bool = False) -> None:
        """
        Store the parent's choice. Turning the model on requires warning_accepted: the parent
        confirmed they read LLM_WARNING. Turning it off withdraws the acceptance, which also
        keeps USE_LLM=true from turning the model on until the warning is accepted again.
        """
        if enabled and not warning_accepted:
            raise ValueError("The warning must be accepted to turn on the language model")
        self._put(db, ENABLED_KEY, "true" if enabled else "false")
        if enabled:
            self._put(db, ACCEPTED_AT_KEY, datetime.now().isoformat(timespec="seconds"))
        else:
            db.query(AppSetting).filter(AppSetting.key == ACCEPTED_AT_KEY).delete()
        db.commit()
        self._enabled = enabled
        self._accepted = enabled
        logger.warning("Language model turned %s from the parent dashboard", "on" if enabled else "off")

    def status(self, db: Session) -> Dict:
        """The setting, the warning, and whether a model file is present, for the dashboard"""
        stored = self.load(db)
        accepted = db.get(AppSetting, ACCEPTED_AT_KEY)
        model_path = settings.get_model_path()
        bundled = bool(settings.BUNDLED_MODEL_PATH) and model_path == Path(settings.BUNDLED_MODEL_PATH).resolve()
        return {
            # On: turned on here or by USE_LLM, with the warning accepted
            "enabled": (stored or settings.USE_LLM) and self._accepted,
            "enabled_by_config": settings.USE_LLM,
            "warning": LLM_WARNING,
            "warning_accepted_at": accepted.value if accepted else None,
            "model_available": model_path.exists(),
            "model_file": model_path.name,
            "bundled_model": bundled and model_path.exists(),
        }

    @staticmethod
    def _put(db: Session, key: str, value: str) -> None:
        row = db.get(AppSetting, key)
        if row:
            row.value = value
        else:
            db.add(AppSetting(key=key, value=value))


llm_setting = LLMSetting()
