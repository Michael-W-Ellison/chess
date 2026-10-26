"""
App Setting Model
Settings for the whole app, changed from the parent dashboard (one row per setting)
"""

from sqlalchemy import Column, String, DateTime
from datetime import datetime

from database.database import Base


class AppSetting(Base):
    """A named setting stored as text ("true", "false", a timestamp)"""

    __tablename__ = "app_settings"

    key = Column(String, primary_key=True)
    value = Column(String, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    def __repr__(self):
        return f"<AppSetting(key={self.key}, value={self.value})>"
