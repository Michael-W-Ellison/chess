"""
Database seeding functions
Populates initial data like advice templates
"""

from sqlalchemy.orm import Session
import logging
import json

logger = logging.getLogger("chatbot.database.seed")


def seed_advice_templates(db: Session) -> None:
    """
    Seed expert-reviewed advice templates into the database

    Args:
        db: Database session
    """
    # Import here to avoid circular dependency
    from models.safety import AdviceTemplate

    # Check if templates already exist
    existing_count = db.query(AdviceTemplate).count()
    if existing_count > 0:
        logger.info(f"Advice templates already seeded ({existing_count} templates)")
        return

    logger.info("Seeding advice templates...")

    templates = [
        # School Stress
        {
            "category": "school_stress",
            "keywords": json.dumps(["test", "homework", "grade", "study", "exam", "project"]),
            "template": "Hey {name}, I know tests can feel really overwhelming! Here's what might help: 1) Break your studying into small chunks - like 20 minutes at a time. 2) Try teaching the material to someone else (even a stuffed animal!). 3) Make sure you get good sleep the night before. You've got this! And remember, one test doesn't define you. Want to talk about what you're most worried about?",
            "min_friendship_level": 1,
            "expert_reviewed": True,
        },
        {
            "category": "school_stress",
            "keywords": json.dumps(["homework", "assignment", "project", "due"]),
            "template": "Homework piling up? I get it, {name}. Try this: make a list of everything you need to do, then tackle the easiest thing first. That little win will give you momentum! Break big projects into tiny steps. And don't forget to take breaks - your brain needs them! You're doing great just by working on it.",
            "min_friendship_level": 2,
            "expert_reviewed": True,
        },
        # Friend Conflict
        {
            "category": "friend_conflict",
            "keywords": json.dumps(["friend", "argument", "fight", "mad at me", "ignoring"]),
            "template": "Friend arguments are really tough, {name}. Here's something that might help: try to see it from their perspective too. Maybe they didn't mean to hurt you, or maybe they're going through something hard. When you're both calm, you could say something like 'I felt hurt when...' instead of 'You did...' That makes it easier to talk about. And hey, real friends can work through disagreements. Give it a little time, okay?",
            "min_friendship_level": 3,
            "expert_reviewed": True,
        },
        {
            "category": "friend_conflict",
            "keywords": json.dumps(["left out", "excluded", "ignored", "not invited"]),
            "template": "Feeling left out really stings, {name}. I'm sorry you're going through this. Sometimes people don't realize they're leaving someone out, or maybe they had limited space. It doesn't mean you're not important! You could try talking to your friend directly about how you feel, or focus on other friendships too. You're an awesome person and deserve friends who include you!",
            "min_friendship_level": 4,
            "expert_reviewed": True,
        },
        # Performance Anxiety
        {
            "category": "performance_anxiety",
            "keywords": json.dumps(["nervous", "scared", "worried", "anxious", "presentation"]),
            "template": "Being nervous is totally normal, {name} - even adults get nervous! Try this: take slow, deep breaths (breathe in for 4, hold for 4, out for 4). Remember that everyone else has probably felt this way too. And here's a secret: a little nervousness can actually help you do better! It means you care. You're going to be great!",
            "min_friendship_level": 2,
            "expert_reviewed": True,
        },
        # Family Issues
        {
            "category": "family_issues",
            "keywords": json.dumps(["parent", "sibling", "mom", "dad", "brother", "sister"]),
            "template": "Family stuff can be complicated, {name}. It's okay to have mixed feelings about family members. If something is bothering you, try talking to a parent or trusted adult when everyone is calm. Use 'I feel' statements like 'I feel sad when...' Sometimes families need help communicating, and that's okay! Would talking to a school counselor help?",
            "min_friendship_level": 5,
            "expert_reviewed": True,
        },
        # Self Confidence
        {
            "category": "self_confidence",
            "keywords": json.dumps(["not good at", "bad at", "everyone else", "I can't"]),
            "template": "Hey {name}, everyone is good at different things! The stuff you find hard might be easy for others, but I bet there are things you're great at that others struggle with. What matters is that you're trying and learning. Making mistakes is how we get better! What's one thing you ARE good at? Let's celebrate that!",
            "min_friendship_level": 3,
            "expert_reviewed": True,
        },
        {
            "category": "self_confidence",
            "keywords": json.dumps(["compare", "better than me", "not as good"]),
            "template": "Comparing yourself to others is a tough habit, {name}. But here's the thing: you're on your own unique journey! Everyone learns and grows at different speeds. Instead of comparing, try competing with yourself - are you better than you were last month? Last year? That's what really matters. You're doing amazing just by being you!",
            "min_friendship_level": 4,
            "expert_reviewed": True,
        },
        # Boredom
        {
            "category": "boredom",
            "keywords": json.dumps(["bored", "nothing to do", "no fun"]),
            "template": "Bored? Let's fix that, {name}! Here are some ideas: 1) Try creating something - draw, write, build. 2) Learn a new skill from YouTube. 3) Go outside and explore. 4) Read a book or start a new series. 5) Help someone with something. Sometimes boredom means your brain is ready for a new challenge! What sounds interesting to you?",
            "min_friendship_level": 1,
            "expert_reviewed": True,
        },
    ]

    # Create template objects
    for template_data in templates:
        template = AdviceTemplate(**template_data)
        db.add(template)

    # Commit all templates
    db.commit()

    logger.info(f"Seeded {len(templates)} advice templates")
