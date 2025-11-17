"""
Test script for Profile Panel memory display

This script populates the database with sample memory data
to test the ProfilePanel UI component's display functionality.

Run this script with the backend server running:
    python backend/test_profile_panel.py

Then open the frontend app and navigate to the Profile tab to verify display.
"""

import sys
import os
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from database.database import SessionLocal, init_db
from services.memory_manager import memory_manager
from models.user import User


def create_test_user(db):
    """Create or get test user"""
    user = db.query(User).filter(User.id == 1).first()

    if not user:
        user = User(id=1, name="Test User")
        db.add(user)
        db.commit()
        print("✓ Created test user (ID: 1)")
    else:
        print("✓ Test user already exists (ID: 1)")

    return user


def populate_favorites(db, user_id):
    """Populate favorites category"""
    print("\n📝 Adding Favorites...")

    favorites = [
        ("color", "blue"),
        ("sport", "soccer"),
        ("food", "pizza"),
        ("animal", "dog"),
        ("subject", "science"),
        ("game", "Minecraft"),
        ("movie", "Spider-Man"),
        ("book", "Harry Potter"),
    ]

    for key, value in favorites:
        memory_manager.add_favorite(user_id, key, value, db)
        print(f"  ⭐ {key}: {value}")

    print(f"✓ Added {len(favorites)} favorites")


def populate_dislikes(db, user_id):
    """Populate dislikes category"""
    print("\n📝 Adding Dislikes...")

    dislikes = [
        ("vegetable", "broccoli"),
        ("weather", "rain"),
        ("subject", "history"),
        ("chore", "cleaning room"),
        ("food", "mushrooms"),
    ]

    for key, value in dislikes:
        memory_manager.add_dislike(user_id, key, value, db)
        print(f"  👎 {key}: {value}")

    print(f"✓ Added {len(dislikes)} dislikes")


def populate_people(db, user_id):
    """Populate people category"""
    print("\n📝 Adding Important People...")

    people = [
        ("friend_emma", "best friend who loves soccer"),
        ("friend_jake", "friend from school who plays Minecraft"),
        ("teacher_smith", "favorite math teacher"),
        ("mom", "helps with homework and bakes cookies"),
        ("dad", "teaches me science experiments"),
        ("sister_lily", "younger sister who likes art"),
        ("coach_martinez", "soccer coach"),
    ]

    for key, value in people:
        memory_manager.add_person(user_id, key, value, db)
        print(f"  👥 {key}: {value}")

    print(f"✓ Added {len(people)} people")


def populate_goals(db, user_id):
    """Populate goals category"""
    print("\n📝 Adding Goals...")

    goals = [
        ("academic", "get all A's this semester"),
        ("sports", "make the varsity soccer team"),
        ("personal", "read 30 books this year"),
        ("fitness", "run a 5k race"),
        ("creative", "learn to play guitar"),
        ("social", "make 3 new friends"),
        ("skill", "learn Python programming"),
    ]

    for key, value in goals:
        memory_manager.add_goal(user_id, key, value, db)
        print(f"  🎯 {key}: {value}")

    print(f"✓ Added {len(goals)} goals")


def populate_achievements(db, user_id):
    """Populate achievements category"""
    print("\n📝 Adding Achievements...")

    achievements = [
        ("academic", "made honor roll last semester"),
        ("sports", "won soccer championship"),
        ("personal", "read 25 books last year"),
        ("creative", "won school art contest"),
        ("community", "volunteered 50 hours"),
        ("skill", "built my first robot"),
    ]

    for key, value in achievements:
        memory_manager.add_achievement(user_id, key, value, db)
        print(f"  🏆 {key}: {value}")

    print(f"✓ Added {len(achievements)} achievements")


def update_mention_counts(db, user_id):
    """Update some memories to have higher mention counts for testing"""
    print("\n📝 Updating mention counts for realistic data...")

    from models.memory import UserProfile

    # Get some memories and update their mention counts
    soccer_fav = db.query(UserProfile).filter(
        UserProfile.user_id == user_id,
        UserProfile.category == "favorite",
        UserProfile.key == "sport"
    ).first()

    if soccer_fav:
        soccer_fav.mention_count = 15
        soccer_fav.last_mentioned = datetime.now() - timedelta(hours=2)
        print(f"  ⚡ Updated 'soccer' favorite - mentioned 15 times")

    pizza_fav = db.query(UserProfile).filter(
        UserProfile.user_id == user_id,
        UserProfile.category == "favorite",
        UserProfile.key == "food"
    ).first()

    if pizza_fav:
        pizza_fav.mention_count = 8
        pizza_fav.last_mentioned = datetime.now() - timedelta(days=1)
        print(f"  ⚡ Updated 'pizza' favorite - mentioned 8 times")

    emma = db.query(UserProfile).filter(
        UserProfile.user_id == user_id,
        UserProfile.category == "person",
        UserProfile.key == "friend_emma"
    ).first()

    if emma:
        emma.mention_count = 12
        emma.last_mentioned = datetime.now() - timedelta(hours=5)
        print(f"  ⚡ Updated Emma - mentioned 12 times")

    db.commit()
    print("✓ Updated mention counts")


def verify_data(db, user_id):
    """Verify all data was created"""
    print("\n📊 Verifying Data...")

    from models.memory import UserProfile

    categories = ["favorite", "dislike", "person", "goal", "achievement"]

    for category in categories:
        count = db.query(UserProfile).filter(
            UserProfile.user_id == user_id,
            UserProfile.category == category
        ).count()

        emoji = {
            "favorite": "⭐",
            "dislike": "👎",
            "person": "👥",
            "goal": "🎯",
            "achievement": "🏆"
        }[category]

        print(f"  {emoji} {category.capitalize()}: {count} items")

    total = db.query(UserProfile).filter(UserProfile.user_id == user_id).count()
    print(f"\n✓ Total memories: {total}")


def main():
    """Main test data population function"""
    print("=" * 60)
    print("Profile Panel Memory Display Test - Data Population")
    print("=" * 60)

    # Initialize database
    init_db()
    db = SessionLocal()

    try:
        # Create test user
        user = create_test_user(db)

        # Populate all categories
        populate_favorites(db, user.id)
        populate_dislikes(db, user.id)
        populate_people(db, user.id)
        populate_goals(db, user.id)
        populate_achievements(db, user.id)

        # Update some mention counts for realism
        update_mention_counts(db, user.id)

        # Verify everything was created
        verify_data(db, user.id)

        print("\n" + "=" * 60)
        print("✅ Test data populated successfully!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Ensure backend server is running (python -m uvicorn main:app)")
        print("2. Start frontend dev server (npm run dev)")
        print("3. Open the app and navigate to Profile tab")
        print("4. Verify all memory categories are displayed correctly")
        print("5. Check all three tabs: Personality, Your Profile, Memories")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
