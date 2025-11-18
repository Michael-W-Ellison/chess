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
        # Homeschool Stress - Social Isolation
        {
            "category": "school",
            "subcategory": "homeschool_stress",
            "keywords": json.dumps(["homeschool", "lonely", "no friends", "isolated", "miss school"]),
            "template": "Hey {name}, I hear you - being homeschooled can sometimes feel lonely. But here's the good news: there are lots of ways to connect! Try joining homeschool co-ops, sports teams, clubs, or online communities for kids who share your interests. Libraries often have programs too! You could also invite kids from your neighborhood to hang out. Being homeschooled doesn't mean being alone - it just means finding friends in different places!",
            "min_friendship_level": 2,
            "min_age": 8,
            "max_age": 14,
            "tone": "supportive",
            "response_style": "encouraging",
            "expert_reviewed": True,
            "context_tags": json.dumps(["homeschool", "social_isolation", "loneliness"]),
        },
        # Homeschool Stress - Self-Motivation
        {
            "category": "school",
            "subcategory": "homeschool_stress",
            "keywords": json.dumps(["homeschool", "focus", "distracted", "motivation", "procrastinate"]),
            "template": "Staying focused at home is hard, {name} - even adults struggle with this! Try these tricks: 1) Create a special study spot that's ONLY for schoolwork. 2) Use a timer - work for 25 minutes, break for 5. 3) Start with the hardest subject when your brain is fresh. 4) Give yourself small rewards for finishing tasks. 5) Put away your phone and other distractions. You're basically the boss of your own learning - pretty cool, right?",
            "min_friendship_level": 3,
            "min_age": 8,
            "max_age": 14,
            "tone": "practical",
            "response_style": "direct",
            "expert_reviewed": True,
            "context_tags": json.dumps(["homeschool", "self_discipline", "focus", "motivation"]),
        },
        # Homeschool Stress - Parent as Teacher
        {
            "category": "family",
            "subcategory": "homeschool_stress",
            "keywords": json.dumps(["homeschool", "parent", "mom", "dad", "teacher", "frustrated"]),
            "template": "Having your parent as your teacher can be tricky sometimes, {name}. It's hard when the person who makes you dinner is also the one explaining math! If you're feeling frustrated, try this: take a break when things get tense, come back when everyone is calmer. Remember, your parents are learning how to teach just like you're learning the subjects. It's okay to say 'Can we try a different way?' or 'I need a break.' You're both doing your best!",
            "min_friendship_level": 4,
            "min_age": 8,
            "max_age": 14,
            "tone": "empathetic",
            "response_style": "validating",
            "expert_reviewed": True,
            "context_tags": json.dumps(["homeschool", "parent_conflict", "family_stress"]),
        },
        # Homeschool Stress - Missing Traditional School
        {
            "category": "emotional",
            "subcategory": "homeschool_stress",
            "keywords": json.dumps(["homeschool", "miss", "regular school", "traditional school", "wish"]),
            "template": "It's totally okay to miss parts of traditional school, {name}. Maybe you miss having lots of classmates, or the school lunch, or special activities. Those feelings are valid! Homeschooling is different, not better or worse - just different. Talk to your parents about what you miss most - maybe you can find ways to get some of those experiences through clubs, classes, or events. And remember, homeschooling has cool perks too - like learning in your pajamas or going on field trips on random Tuesdays!",
            "min_friendship_level": 3,
            "min_age": 8,
            "max_age": 14,
            "tone": "empathetic",
            "response_style": "validating",
            "expert_reviewed": True,
            "context_tags": json.dumps(["homeschool", "nostalgia", "school_experience"]),
        },
        # Homeschool Stress - Structure and Independence
        {
            "category": "school",
            "subcategory": "homeschool_stress",
            "keywords": json.dumps(["homeschool", "schedule", "routine", "structure", "organize"]),
            "template": "Finding the right balance between freedom and structure is one of the trickiest parts of homeschooling, {name}! Here's what might help: create a daily routine (but keep it flexible), use a planner to track assignments, set small goals for each day. Too much freedom can feel overwhelming, but too much structure can feel boring. Work with your parents to find YOUR perfect balance. What works for other homeschoolers might not work for you - and that's okay!",
            "min_friendship_level": 3,
            "min_age": 9,
            "max_age": 14,
            "tone": "practical",
            "response_style": "direct",
            "expert_reviewed": True,
            "context_tags": json.dumps(["homeschool", "time_management", "organization"]),
        },
        # Homeschool Stress - Distractions at Home
        {
            "category": "school",
            "subcategory": "homeschool_stress",
            "keywords": json.dumps(["homeschool", "distracted", "siblings", "noise", "interruptions"]),
            "template": "I get it, {name} - when your classroom is also your home, distractions are everywhere! Your siblings, pets, the TV, your bed calling your name... Try this: 1) Find a quiet spot just for school (even a corner works!). 2) Use headphones with focus music or white noise. 3) Set 'do not disturb' times with your family. 4) Put away toys and games during school hours. Sometimes you might need to speak up: 'I need quiet time to focus right now.' It's okay to protect your learning space!",
            "min_friendship_level": 2,
            "min_age": 8,
            "max_age": 13,
            "tone": "supportive",
            "response_style": "practical",
            "expert_reviewed": True,
            "context_tags": json.dumps(["homeschool", "distractions", "focus", "environment"]),
        },
        # Homeschool Stress - Being Different
        {
            "category": "social",
            "subcategory": "homeschool_stress",
            "keywords": json.dumps(["homeschool", "different", "weird", "explain", "don't understand"]),
            "template": "When people ask about homeschooling and don't get it, that can feel awkward, right {name}? Here's the thing: different doesn't mean wrong! You could say something simple like 'I do school at home with my parents. It's pretty cool because...' and share what YOU like about it. Not everyone will understand, and that's okay. You don't have to convince anyone. The people who matter will accept you no matter where you go to school. You're unique - and that's actually awesome!",
            "min_friendship_level": 4,
            "min_age": 9,
            "max_age": 14,
            "tone": "encouraging",
            "response_style": "validating",
            "expert_reviewed": True,
            "context_tags": json.dumps(["homeschool", "social_acceptance", "being_different"]),
        },
        # Homeschool Stress - Time Management
        {
            "category": "school",
            "subcategory": "homeschool_stress",
            "keywords": json.dumps(["homeschool", "time", "deadline", "finish", "behind"]),
            "template": "Time management without bells and schedules can be tough, {name}! Try this system: 1) Write down all your tasks for the week. 2) Estimate how long each will take (then add a little extra - we're all optimistic!). 3) Schedule the hardest stuff for when you have the most energy. 4) Use timers to stay on track. 5) Build in buffer time for the unexpected. Remember, homeschooling is flexible - if something takes longer than planned, you can adjust! The goal is learning, not racing the clock.",
            "min_friendship_level": 3,
            "min_age": 10,
            "max_age": 14,
            "tone": "practical",
            "response_style": "direct",
            "expert_reviewed": True,
            "context_tags": json.dumps(["homeschool", "time_management", "organization", "deadlines"]),
        },
        # Homeschool Stress - Missing Activities
        {
            "category": "emotional",
            "subcategory": "homeschool_stress",
            "keywords": json.dumps(["homeschool", "miss", "activities", "sports", "clubs", "events"]),
            "template": "Missing out on school dances, sports teams, or clubs can feel really sad, {name}. I'm sorry you're feeling this way. Good news though - you can still do many of these things! Look for: community sports leagues, music or art classes, 4-H clubs, Scout groups, homeschool co-op activities, library programs, volunteer opportunities. Many communities have versions of school activities that are open to everyone! Talk to your parents about what you miss most - they might be able to help you find similar experiences.",
            "min_friendship_level": 4,
            "min_age": 8,
            "max_age": 14,
            "tone": "empathetic",
            "response_style": "supportive",
            "expert_reviewed": True,
            "context_tags": json.dumps(["homeschool", "extracurricular", "social_activities"]),
        },
        # Homeschool Stress - Learning Style Mismatch
        {
            "category": "school",
            "subcategory": "homeschool_stress",
            "keywords": json.dumps(["homeschool", "don't understand", "learning", "teaching", "curriculum"]),
            "template": "If the way your parents are teaching something isn't clicking for you, {name}, that doesn't mean you're not smart! Everyone learns differently. Some people need to see things, some need to hear them, some need to DO them. Try telling your parents: 'This isn't making sense to me. Can we try it a different way?' There are SO many resources - videos, apps, books, hands-on activities. One of the cool things about homeschooling is you can customize how you learn. You're allowed to ask for what you need!",
            "min_friendship_level": 4,
            "min_age": 9,
            "max_age": 14,
            "tone": "encouraging",
            "response_style": "validating",
            "expert_reviewed": True,
            "context_tags": json.dumps(["homeschool", "learning_style", "communication", "education"]),
        },
    ]

    # Create template objects
    for template_data in templates:
        template = AdviceTemplate(**template_data)
        db.add(template)

    # Commit all templates
    db.commit()

    logger.info(f"Seeded {len(templates)} advice templates")
