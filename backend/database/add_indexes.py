"""
Database Index Optimization
Adds indexes to improve query performance on frequently accessed columns
"""

from sqlalchemy import create_index, Index
from database.database import engine, Base
from models import (
    User,
    Conversation,
    Message,
    UserProfile,
    BotPersonality,
    SafetyFlag,
    LevelUpEvent,
    PersonalityDrift
)
import logging

logger = logging.getLogger("chatbot.database")


def add_indexes():
    """
    Add database indexes for performance optimization

    Indexes are added to columns that are frequently used in:
    - WHERE clauses (filtering)
    - JOIN conditions
    - ORDER BY clauses
    - Foreign key relationships
    """

    logger.info("Starting database index optimization...")

    with engine.connect() as conn:
        # Track index creation
        created_indexes = []

        try:
            # ============================================================================
            # CONVERSATIONS TABLE INDEXES
            # ============================================================================

            # Index on user_id (foreign key) - commonly filtered by user
            try:
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id)"
                )
                created_indexes.append("idx_conversations_user_id")
            except Exception as e:
                logger.warning(f"Could not create idx_conversations_user_id: {e}")

            # Index on timestamp - for ordering/filtering by date
            try:
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON conversations(timestamp DESC)"
                )
                created_indexes.append("idx_conversations_timestamp")
            except Exception as e:
                logger.warning(f"Could not create idx_conversations_timestamp: {e}")

            # Composite index for user + timestamp (most common query pattern)
            try:
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_conversations_user_timestamp ON conversations(user_id, timestamp DESC)"
                )
                created_indexes.append("idx_conversations_user_timestamp")
            except Exception as e:
                logger.warning(f"Could not create idx_conversations_user_timestamp: {e}")

            # ============================================================================
            # MESSAGES TABLE INDEXES
            # ============================================================================

            # Index on conversation_id (foreign key) - always filtered by conversation
            try:
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id)"
                )
                created_indexes.append("idx_messages_conversation_id")
            except Exception as e:
                logger.warning(f"Could not create idx_messages_conversation_id: {e}")

            # Index on timestamp - for ordering messages
            try:
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)"
                )
                created_indexes.append("idx_messages_timestamp")
            except Exception as e:
                logger.warning(f"Could not create idx_messages_timestamp: {e}")

            # Composite index for conversation + timestamp (most common pattern)
            try:
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_messages_conv_timestamp ON messages(conversation_id, timestamp)"
                )
                created_indexes.append("idx_messages_conv_timestamp")
            except Exception as e:
                logger.warning(f"Could not create idx_messages_conv_timestamp: {e}")

            # Index on flagged - for finding flagged messages
            try:
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_messages_flagged ON messages(flagged) WHERE flagged = 1"
                )
                created_indexes.append("idx_messages_flagged")
            except Exception as e:
                logger.warning(f"Could not create idx_messages_flagged: {e}")

            # Index on role - for filtering user vs assistant messages
            try:
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_messages_role ON messages(role)"
                )
                created_indexes.append("idx_messages_role")
            except Exception as e:
                logger.warning(f"Could not create idx_messages_role: {e}")

            # ============================================================================
            # USER_PROFILE (MEMORY) TABLE INDEXES
            # ============================================================================

            # Index on user_id (foreign key)
            try:
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_user_profile_user_id ON user_profile(user_id)"
                )
                created_indexes.append("idx_user_profile_user_id")
            except Exception as e:
                logger.warning(f"Could not create idx_user_profile_user_id: {e}")

            # Composite index on user_id + category (very common query pattern)
            try:
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_user_profile_user_category ON user_profile(user_id, category)"
                )
                created_indexes.append("idx_user_profile_user_category")
            except Exception as e:
                logger.warning(f"Could not create idx_user_profile_user_category: {e}")

            # Index on last_mentioned - for finding recently mentioned items
            try:
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_user_profile_last_mentioned ON user_profile(last_mentioned DESC)"
                )
                created_indexes.append("idx_user_profile_last_mentioned")
            except Exception as e:
                logger.warning(f"Could not create idx_user_profile_last_mentioned: {e}")

            # Index on mention_count - for finding frequently mentioned items
            try:
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_user_profile_mention_count ON user_profile(mention_count DESC)"
                )
                created_indexes.append("idx_user_profile_mention_count")
            except Exception as e:
                logger.warning(f"Could not create idx_user_profile_mention_count: {e}")

            # ============================================================================
            # USERS TABLE INDEXES
            # ============================================================================

            # Index on last_active - for finding recent users
            try:
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_users_last_active ON users(last_active DESC)"
                )
                created_indexes.append("idx_users_last_active")
            except Exception as e:
                logger.warning(f"Could not create idx_users_last_active: {e}")

            # Index on created_at - for finding new users
            try:
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC)"
                )
                created_indexes.append("idx_users_created_at")
            except Exception as e:
                logger.warning(f"Could not create idx_users_created_at: {e}")

            # ============================================================================
            # SAFETY_FLAGS TABLE INDEXES
            # ============================================================================

            # Index on user_id - for finding all flags for a user
            try:
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_safety_flags_user_id ON safety_flags(user_id)"
                )
                created_indexes.append("idx_safety_flags_user_id")
            except Exception as e:
                logger.warning(f"Could not create idx_safety_flags_user_id: {e}")

            # Index on severity - for finding high-severity flags
            try:
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_safety_flags_severity ON safety_flags(severity)"
                )
                created_indexes.append("idx_safety_flags_severity")
            except Exception as e:
                logger.warning(f"Could not create idx_safety_flags_severity: {e}")

            # Index on timestamp - for recent flags
            try:
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_safety_flags_timestamp ON safety_flags(timestamp DESC)"
                )
                created_indexes.append("idx_safety_flags_timestamp")
            except Exception as e:
                logger.warning(f"Could not create idx_safety_flags_timestamp: {e}")

            # ============================================================================
            # LEVEL_UP_EVENTS TABLE INDEXES
            # ============================================================================

            # Index on user_id + timestamp - for user's level history
            try:
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_level_up_events_user_timestamp ON level_up_events(user_id, timestamp DESC)"
                )
                created_indexes.append("idx_level_up_events_user_timestamp")
            except Exception as e:
                logger.warning(f"Could not create idx_level_up_events_user_timestamp: {e}")

            # ============================================================================
            # PERSONALITY_DRIFT TABLE INDEXES
            # ============================================================================

            # Index on user_id + timestamp - for user's personality history
            try:
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_personality_drift_user_timestamp ON personality_drift(user_id, timestamp DESC)"
                )
                created_indexes.append("idx_personality_drift_user_timestamp")
            except Exception as e:
                logger.warning(f"Could not create idx_personality_drift_user_timestamp: {e}")

            # Commit all changes
            conn.commit()

            logger.info(f"✓ Successfully created {len(created_indexes)} indexes:")
            for idx_name in created_indexes:
                logger.info(f"  - {idx_name}")

            return created_indexes

        except Exception as e:
            logger.error(f"Error creating indexes: {e}", exc_info=True)
            conn.rollback()
            return created_indexes


def analyze_database():
    """
    Run ANALYZE on the database to update statistics for query optimization
    SQLite uses these statistics to choose the best query plan
    """
    logger.info("Running ANALYZE on database...")

    try:
        with engine.connect() as conn:
            conn.execute("ANALYZE")
            conn.commit()
            logger.info("✓ Database analysis complete")
            return True
    except Exception as e:
        logger.error(f"Error analyzing database: {e}", exc_info=True)
        return False


def get_index_info():
    """
    Get information about all indexes in the database

    Returns:
        List of tuples: (table_name, index_name, columns)
    """
    logger.info("Retrieving index information...")

    indexes = []

    try:
        with engine.connect() as conn:
            # Get all indexes
            result = conn.execute(
                "SELECT name, tbl_name, sql FROM sqlite_master WHERE type='index' ORDER BY tbl_name, name"
            )

            for row in result:
                index_name = row[0]
                table_name = row[1]
                sql = row[2]

                # Skip auto-created indexes
                if sql is None or index_name.startswith("sqlite_"):
                    continue

                indexes.append({
                    "name": index_name,
                    "table": table_name,
                    "sql": sql
                })

            logger.info(f"Found {len(indexes)} custom indexes")
            return indexes

    except Exception as e:
        logger.error(f"Error getting index info: {e}", exc_info=True)
        return []


if __name__ == "__main__":
    """Run index optimization when executed directly"""
    import sys
    from utils.logging_config import setup_logging

    # Setup logging
    logger = setup_logging()

    print("=" * 70)
    print("Database Index Optimization")
    print("=" * 70)
    print()

    # Create indexes
    created = add_indexes()
    print(f"\nCreated {len(created)} indexes")

    # Analyze database
    if analyze_database():
        print("\nDatabase analysis complete - statistics updated")

    # Show all indexes
    print("\n" + "=" * 70)
    print("Current Database Indexes")
    print("=" * 70)

    indexes = get_index_info()
    for idx in indexes:
        print(f"\nTable: {idx['table']}")
        print(f"  Index: {idx['name']}")
        print(f"  SQL: {idx['sql']}")

    print("\n" + "=" * 70)
    print("Index optimization complete!")
    print("=" * 70)
