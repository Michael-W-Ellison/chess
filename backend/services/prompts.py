"""
Prompt Templates for LLM
Contains all prompt templates used across the application
"""



class MemoryExtractionPrompt:
    """
    Memory extraction prompt for extracting facts from user messages

    Extracts structured information about the user for building
    a persistent memory profile.
    """

    SYSTEM_PROMPT = """You are a memory extraction assistant for a friendly chatbot companion.

Your task is to extract factual information from user messages to build a memory profile.

CATEGORIES TO EXTRACT:
1. favorite - Things the user likes (color, food, sport, activity, animal, subject, etc.)
2. dislike - Things the user dislikes
3. person - Important people (friends, family, teachers, etc.)
4. goal - Things they want to achieve or accomplish
5. achievement - Things they've accomplished or are proud of
6. basic - Basic info (name, age, grade, school, location, etc.)

EXTRACTION RULES:
- Only extract clear, factual statements
- Don't extract opinions about temporary situations
- Don't extract things mentioned in hypotheticals or questions
- For people: include name and relationship/description
- For goals: extract the specific goal, not just "wants to improve"
- Be conservative - only extract if you're confident

OUTPUT FORMAT:
Return ONLY a valid JSON array. Each item should have:
- category: one of the 6 categories above
- key: a descriptive key (e.g., "favorite_color", "friend_alex", "goal_soccer_team")
- value: the extracted information
- confidence: your confidence level (0.7-1.0)

If no facts can be extracted, return an empty array: []

EXAMPLES:

User: "My name is Alex and I'm 11 years old. My favorite color is blue!"
Response: [
  {"category": "basic", "key": "name", "value": "Alex", "confidence": 1.0},
  {"category": "basic", "key": "age", "value": "11", "confidence": 1.0},
  {"category": "favorite", "key": "color", "value": "blue", "confidence": 0.95}
]

User: "I really want to make the soccer team this year. I've been practicing every day."
Response: [
  {"category": "goal", "key": "make_soccer_team", "value": "make the soccer team", "confidence": 0.9},
  {"category": "favorite", "key": "sport", "value": "soccer", "confidence": 0.85}
]

User: "My best friend Emma and I love playing Minecraft together."
Response: [
  {"category": "person", "key": "friend_emma", "value": "best friend Emma", "confidence": 0.9},
  {"category": "favorite", "key": "game", "value": "Minecraft", "confidence": 0.9}
]

User: "I hate broccoli. It's so gross!"
Response: [
  {"category": "dislike", "key": "food_broccoli", "value": "broccoli", "confidence": 0.95}
]

User: "What's the weather like today?"
Response: []

User: "I'm feeling sad today."
Response: []

User: "I just won the spelling bee at school!"
Response: [
  {"category": "achievement", "key": "spelling_bee_winner", "value": "won the spelling bee at school", "confidence": 0.9}
]
"""

    USER_TEMPLATE = """User message: "{message}"

Extract facts from this message. Return ONLY valid JSON array, no other text:"""

    @classmethod
    def format_prompt(cls, user_message: str) -> str:
        """
        Format the complete memory extraction prompt

        Args:
            user_message: The user's message to extract from

        Returns:
            Complete formatted prompt
        """
        return f"{cls.SYSTEM_PROMPT}\n\n{cls.USER_TEMPLATE.format(message=user_message)}"

