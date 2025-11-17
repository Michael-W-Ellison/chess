"""
Database configuration and session management
SQLAlchemy setup for SQLite database
"""

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import logging

from utils.config import settings

logger = logging.getLogger("chatbot.database")

# Create SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    pool_pre_ping=True,  # Verify connections before using
)


# Enable foreign keys for SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable foreign key constraints in SQLite"""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# Create SessionLocal class for database sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Create declarative base for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for getting database sessions in FastAPI endpoints

    Usage:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            # Use db here
            pass

    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize the database
    Creates all tables defined in models
    Should be called on application startup
    """
    logger.info("Initializing database...")

    # Import all models here to ensure they are registered with Base
    # This must be done before create_all() is called
    from models import (
        user,
        personality,
        conversation,
        memory,
        safety,
        level_up_event,
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    logger.info(f"Database initialized at {settings.get_database_path()}")

    # Seed initial data if needed
    db = SessionLocal()
    try:
        seed_initial_data(db)
    finally:
        db.close()


def close_db() -> None:
    """
    Close database connection
    Should be called on application shutdown
    """
    logger.info("Closing database connection...")
    engine.dispose()
    logger.info("Database connection closed")


def seed_initial_data(db: Session) -> None:
    """
    Seed initial data into the database
    - Default advice templates
    - Any other necessary initial data

    Args:
        db: Database session
    """
    from database.seed import seed_advice_templates

    logger.info("Checking for initial data...")

    # Seed advice templates
    seed_advice_templates(db)

    logger.info("Initial data check complete")


def reset_database() -> None:
    """
    WARNING: Drops all tables and recreates them
    USE ONLY FOR DEVELOPMENT/TESTING

    This will delete all data!
    """
    logger.warning("Resetting database - all data will be lost!")

    # Import models
    from models import (
        user,
        personality,
        conversation,
        memory,
        safety,
        level_up_event,
    )

    # Drop all tables
    Base.metadata.drop_all(bind=engine)
    logger.info("All tables dropped")

    # Recreate all tables
    Base.metadata.create_all(bind=engine)
    logger.info("All tables recreated")

    # Seed initial data
    db = SessionLocal()
    try:
        seed_initial_data(db)
    finally:
        db.close()

    logger.info("Database reset complete")
