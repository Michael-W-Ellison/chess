#!/usr/bin/env python3
"""
Database Management Script
Provides commands to seed, reset, and manage the database
"""

import sys
import os
from pathlib import Path

# Add parent directory to path so we can import from backend
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
import logging
from database.database import init_db, reset_database, SessionLocal, seed_initial_data
from database.seed import seed_advice_templates
from models.safety import AdviceTemplate

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def seed_db():
    """Seed the database with initial data"""
    logger.info("Seeding database...")

    db = SessionLocal()
    try:
        seed_initial_data(db)
        logger.info("✓ Database seeded successfully")
    except Exception as e:
        logger.error(f"✗ Error seeding database: {e}")
        raise
    finally:
        db.close()


def reset_db():
    """Reset the database (WARNING: Deletes all data)"""
    logger.warning("⚠️  WARNING: This will delete ALL data in the database!")
    response = input("Are you sure you want to continue? (yes/no): ")

    if response.lower() != 'yes':
        logger.info("Reset cancelled")
        return

    try:
        reset_database()
        logger.info("✓ Database reset successfully")
    except Exception as e:
        logger.error(f"✗ Error resetting database: {e}")
        raise


def init_database():
    """Initialize the database (creates tables if they don't exist)"""
    logger.info("Initializing database...")

    try:
        init_db()
        logger.info("✓ Database initialized successfully")
    except Exception as e:
        logger.error(f"✗ Error initializing database: {e}")
        raise


def show_stats():
    """Show database statistics"""
    logger.info("Database Statistics:")

    db = SessionLocal()
    try:
        # Count advice templates
        template_count = db.query(AdviceTemplate).count()
        logger.info(f"  Advice Templates: {template_count}")

        # Count by category
        categories = db.query(
            AdviceTemplate.category,
            AdviceTemplate.subcategory
        ).distinct().all()

        logger.info(f"  Categories:")
        category_counts = {}
        for category, subcategory in categories:
            if subcategory:
                key = f"{category}/{subcategory}"
            else:
                key = category

            count = db.query(AdviceTemplate).filter(
                AdviceTemplate.category == category,
                AdviceTemplate.subcategory == subcategory
            ).count()
            category_counts[key] = count

        for cat, count in sorted(category_counts.items()):
            logger.info(f"    {cat}: {count}")

        # Count expert reviewed
        expert_reviewed_count = db.query(AdviceTemplate).filter(
            AdviceTemplate.expert_reviewed == True
        ).count()
        logger.info(f"  Expert Reviewed: {expert_reviewed_count}/{template_count}")

    except Exception as e:
        logger.error(f"✗ Error getting statistics: {e}")
        raise
    finally:
        db.close()


def list_templates(category=None, subcategory=None, limit=None):
    """List advice templates"""
    logger.info("Advice Templates:")

    db = SessionLocal()
    try:
        query = db.query(AdviceTemplate)

        if category:
            query = query.filter(AdviceTemplate.category == category)

        if subcategory:
            query = query.filter(AdviceTemplate.subcategory == subcategory)

        if limit:
            query = query.limit(limit)

        templates = query.all()

        for i, template in enumerate(templates, 1):
            cat = f"{template.category}/{template.subcategory}" if template.subcategory else template.category
            logger.info(f"  {i}. [{cat}] FL:{template.min_friendship_level} Age:{template.min_age}-{template.max_age}")
            logger.info(f"     {template.template[:100]}...")
            if template.tone:
                logger.info(f"     Tone: {template.tone}, Style: {template.response_style}")

        logger.info(f"\nTotal: {len(templates)} templates")

    except Exception as e:
        logger.error(f"✗ Error listing templates: {e}")
        raise
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="Database Management Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python manage_db.py init          # Initialize database
  python manage_db.py seed          # Seed database with initial data
  python manage_db.py reset         # Reset database (deletes all data)
  python manage_db.py stats         # Show database statistics
  python manage_db.py list          # List all templates
  python manage_db.py list --category emotional --limit 10  # List specific templates
        """
    )

    parser.add_argument(
        'command',
        choices=['init', 'seed', 'reset', 'stats', 'list'],
        help='Command to execute'
    )

    parser.add_argument(
        '--category',
        help='Filter by category (for list command)'
    )

    parser.add_argument(
        '--subcategory',
        help='Filter by subcategory (for list command)'
    )

    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of results (for list command)'
    )

    args = parser.parse_args()

    try:
        if args.command == 'init':
            init_database()
        elif args.command == 'seed':
            seed_db()
        elif args.command == 'reset':
            reset_db()
        elif args.command == 'stats':
            show_stats()
        elif args.command == 'list':
            list_templates(
                category=args.category,
                subcategory=args.subcategory,
                limit=args.limit
            )
    except Exception as e:
        logger.error(f"Command failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
