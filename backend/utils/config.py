"""
Configuration management using Pydantic Settings
Loads configuration from environment variables and .env file
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""

    # Server Configuration
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEBUG: bool = True

    # Database Configuration
    DATABASE_URL: str = "sqlite:///./data/chatbot.db"

    # LLM Configuration
    MODEL_PATH: str = "./models/llama-3.2-3b-instruct.gguf"
    MODEL_CONTEXT_LENGTH: int = 2048
    MODEL_MAX_TOKENS: int = 512
    MODEL_TEMPERATURE: float = 0.7
    MODEL_N_GPU_LAYERS: int = 0  # 0 for CPU, -1 for full GPU

    # Safety Configuration
    ENABLE_SAFETY_FILTER: bool = True
    LOG_SAFETY_EVENTS: bool = True

    # Email Configuration (for parent notifications)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None

    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/chatbot.log"

    # Feature Flags
    ENABLE_VECTOR_MEMORY: bool = False  # ChromaDB for semantic search
    ENABLE_WEEKLY_REPORTS: bool = True

    # Security
    PARENT_DASHBOARD_REQUIRE_PASSWORD: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    def get_model_path(self) -> Path:
        """Get absolute path to model file"""
        return Path(self.MODEL_PATH).resolve()

    def get_database_path(self) -> Path:
        """Get absolute path to database file"""
        if self.DATABASE_URL.startswith("sqlite:///"):
            db_path = self.DATABASE_URL.replace("sqlite:///", "")
            return Path(db_path).resolve()
        return Path("./data/chatbot.db")

    def ensure_directories(self) -> None:
        """Ensure required directories exist"""
        # Data directory for database
        data_dir = Path("./data")
        data_dir.mkdir(exist_ok=True)

        # Logs directory
        log_dir = Path("./logs")
        log_dir.mkdir(exist_ok=True)

        # Models directory (user needs to download models)
        models_dir = Path("./models")
        models_dir.mkdir(exist_ok=True)


# Create global settings instance
settings = Settings()

# Ensure directories exist
settings.ensure_directories()
