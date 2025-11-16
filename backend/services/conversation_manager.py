"""
Conversation Manager Service
Orchestrates the conversation flow and message processing
"""

from typing import Dict, Optional
import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from models.user import User
from models.personality import BotPersonality
from models.conversation import Conversation, Message

from services.llm_service import llm_service
from services.safety_filter import safety_filter
from services.memory_manager import memory_manager
from services.personality_manager import personality_manager

logger = logging.getLogger("chatbot.conversation_manager")


class ConversationManager:
    """
    Conversation Manager - orchestrates the complete conversation flow

    Responsibilities:
    - Start/end conversations
    - Process user messages through safety filter
    - Build context from personality and memories
    - Generate LLM prompts
    - Generate responses using LLM
    - Extract and store memories
    - Update personality based on conversation
    """

    def __init__(self):
        self.current_conversation_id: Optional[int] = None
        self.message_count = 0
        self.conversation_start_time: Optional[datetime] = None

    def start_conversation(self, user_id: int, db: Session) -> Dict:
        """
        Start a new conversation session

        Args:
            user_id: User ID
            db: Database session

        Returns:
            Dictionary with conversation info and greeting
        """
        # Get or create user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            # Create new user
            user = User(id=user_id, name="User", created_at=datetime.now())
            db.add(user)
            db.commit()
            db.refresh(user)

        # Get or create personality
        personality = (
            db.query(BotPersonality).filter(BotPersonality.user_id == user_id).first()
        )
        if not personality:
            personality = personality_manager.initialize_personality(user_id, db)

        # Create new conversation
        conversation = Conversation(
            user_id=user_id, timestamp=datetime.now(), message_count=0
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        self.current_conversation_id = conversation.id
        self.message_count = 0
        self.conversation_start_time = datetime.now()

        # Update user's last active
        user.last_active = datetime.now()
        db.commit()

        # Generate greeting based on time since last conversation
        greeting = self._generate_greeting(user, personality, db)

        logger.info(f"Started conversation {conversation.id} for user {user_id}")

        return {
            "conversation_id": conversation.id,
            "greeting": greeting,
            "personality": {
                "name": personality.name,
                "mood": personality.mood,
                "friendship_level": personality.friendship_level,
            },
        }

    def process_message(
        self, user_message: str, conversation_id: int, user_id: int, db: Session
    ) -> Dict:
        """
        Process a user message and generate a response

        Args:
            user_message: The user's message
            conversation_id: Current conversation ID
            user_id: User ID
            db: Database session

        Returns:
            Dictionary with response and metadata
        """
        # 1. Safety check
        safety_result = safety_filter.check_message(user_message)

        if safety_result["severity"] == "critical":
            # Handle crisis
            response = self._handle_crisis(safety_result, user_id, db)

            # Store the message and response
            self._store_message(conversation_id, "user", user_message, db, flagged=True)
            self._store_message(conversation_id, "assistant", response, db)

            return {
                "content": response,
                "metadata": {
                    "safety_flag": True,
                    "severity": "critical",
                    "crisis_response": True,
                },
            }

        # 2. Store user message
        user_msg = self._store_message(conversation_id, "user", user_message, db)
        self.message_count += 1

        # 3. Extract and store memories
        memory_manager.extract_and_store_memories(user_message, user_id, db)

        # 4. Get personality
        personality = (
            db.query(BotPersonality).filter(BotPersonality.user_id == user_id).first()
        )

        # 5. Build context
        context = self._build_context(user_message, user_id, personality, db)

        # 6. Generate response
        if llm_service.is_loaded:
            prompt = self._build_prompt(context, user_message, personality)
            raw_response = llm_service.generate(prompt, max_tokens=150, temperature=0.7)
        else:
            raw_response = self._fallback_response(context)

        # 7. Apply personality to response
        final_response = self._apply_personality_filter(raw_response, personality)

        # 8. Safety check on response (optional)
        response_safety = safety_filter.check_message(final_response)
        if not response_safety["safe"]:
            final_response = (
                "Hmm, I'm not sure how to respond to that. Want to talk about something else?"
            )

        # 9. Store assistant response
        self._store_message(conversation_id, "assistant", final_response, db)

        # 10. Update conversation count
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conversation:
            conversation.message_count = self.message_count
            db.commit()

        return {
            "content": final_response,
            "metadata": {
                "safety_flag": safety_result["severity"] != "none",
                "mood_detected": context.get("detected_mood"),
                "topics_extracted": context.get("keywords", []),
            },
        }

    def end_conversation(self, conversation_id: int, db: Session) -> None:
        """
        End a conversation and perform cleanup

        Args:
            conversation_id: Conversation ID
            db: Database session
        """
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation:
            logger.warning(f"Conversation {conversation_id} not found")
            return

        # Calculate duration
        if self.conversation_start_time:
            duration = (datetime.now() - self.conversation_start_time).seconds
            conversation.duration_seconds = duration

        conversation.message_count = self.message_count

        # Generate summary (simplified for now)
        messages = (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id, Message.role == "user")
            .all()
        )

        if messages:
            # Extract keywords from all messages
            all_text = " ".join([m.content for m in messages])
            keywords = memory_manager.extract_keywords(all_text)
            conversation.conversation_summary = f"Discussed: {', '.join(keywords[:5])}"

        # Update personality
        personality = (
            db.query(BotPersonality)
            .filter(BotPersonality.user_id == conversation.user_id)
            .first()
        )

        if personality:
            # Increment conversation count
            personality.total_conversations += 1

            # Calculate conversation metrics
            metrics = self._calculate_conversation_metrics(conversation_id, db)

            # Update traits based on conversation
            personality_manager.update_personality_traits(personality, metrics, db)

            # Check for friendship level increase
            personality, level_increased = personality_manager.update_friendship_level(
                personality, db
            )

            if level_increased:
                logger.info(
                    f"User {conversation.user_id} reached friendship level {personality.friendship_level}!"
                )

        db.commit()

        logger.info(
            f"Ended conversation {conversation_id}: "
            f"{self.message_count} messages, {conversation.duration_seconds}s"
        )

        # Reset state
        self.current_conversation_id = None
        self.message_count = 0
        self.conversation_start_time = None

    def _generate_greeting(
        self, user: User, personality: BotPersonality, db: Session
    ) -> str:
        """Generate appropriate greeting based on time since last chat"""
        # Get hours since last conversation
        last_conversation = (
            db.query(Conversation)
            .filter(Conversation.user_id == user.id)
            .order_by(Conversation.timestamp.desc())
            .first()
        )

        if last_conversation:
            hours_since = (datetime.now() - last_conversation.timestamp).seconds / 3600
        else:
            hours_since = 999  # First conversation

        name = user.name or "there"

        if hours_since > 48:
            return f"Hey {name}! I missed you! It's been a while. How have you been?"
        elif hours_since > 24:
            return f"Hi {name}! Good to see you again! How was your day?"
        elif hours_since < 1:
            return f"Hey {name}! Back already? What's up?"
        else:
            return f"Hey {name}! How are you doing?"

    def _build_context(
        self,
        user_message: str,
        user_id: int,
        personality: BotPersonality,
        db: Session,
    ) -> Dict:
        """Build conversation context"""
        # Extract keywords from user message
        keywords = memory_manager.extract_keywords(user_message)

        # Get relevant memories
        memories = memory_manager.get_relevant_memories(user_id, keywords, db, limit=5)

        # Get recent messages
        if self.current_conversation_id:
            recent_messages = (
                db.query(Message)
                .filter(Message.conversation_id == self.current_conversation_id)
                .order_by(Message.timestamp.desc())
                .limit(10)
                .all()
            )
            recent_messages.reverse()  # Chronological order
        else:
            recent_messages = []

        # Detect user mood (simple)
        detected_mood = self._detect_user_mood(user_message)

        return {
            "personality": personality,
            "keywords": keywords,
            "relevant_memories": memories,
            "recent_messages": recent_messages,
            "detected_mood": detected_mood,
        }

    def _build_prompt(
        self, context: Dict, user_message: str, personality: BotPersonality
    ) -> str:
        """Build LLM prompt with personality and context"""
        # Get user info
        user_name = "friend"  # Default, could be extracted from memories

        # Get personality descriptions
        trait_descs = personality_manager.get_personality_description(personality)

        # Build system prompt
        system = f"""You are {personality.name}, a friendly AI companion for a preteen child.

PERSONALITY TRAITS:
- Humor: {trait_descs['humor']} ({personality.humor:.1f}/1.0)
- Energy: {trait_descs['energy']} ({personality.energy:.1f}/1.0)
- Curiosity: {trait_descs['curiosity']} ({personality.curiosity:.1f}/1.0)
- Communication: {trait_descs['formality']}

CURRENT MOOD: {personality.mood}

YOUR QUIRKS: {', '.join(personality.get_quirks())}
YOUR INTERESTS: {', '.join(personality.get_interests())}

FRIENDSHIP LEVEL: {personality.friendship_level}/10
Total conversations together: {personality.total_conversations}
"""

        # Add memories if available
        memories = context.get("relevant_memories", [])
        if memories:
            memory_text = memory_manager.format_memories_for_prompt(memories)
            system += f"\n\nWHAT YOU REMEMBER ABOUT THEM:\n{memory_text}\n"

        # Add instructions
        system += """
INSTRUCTIONS:
- Respond naturally as a friend would
- Use age-appropriate language (preteen level)
- Keep responses 2-4 sentences
- Be supportive, kind, and encouraging
- Reference past conversations when relevant
- Never pretend to be human - you're an AI friend
- Encourage healthy behaviors and real friendships
"""

        # Build conversation history
        history = ""
        for msg in context.get("recent_messages", [])[-6:]:
            role_name = "User" if msg.role == "user" else personality.name
            history += f"{role_name}: {msg.content}\n"

        # Full prompt
        prompt = f"{system}\n\n{history}User: {user_message}\n{personality.name}:"

        return prompt

    def _apply_personality_filter(
        self, response: str, personality: BotPersonality
    ) -> str:
        """Apply personality quirks to response"""
        import random

        quirks = personality.get_quirks()

        # Add emoji if quirk enabled
        if "uses_emojis" in quirks and random.random() < 0.4:
            emoji_map = {
                "happy": ["😊", "🙂", "😄"],
                "excited": ["🎉", "😃", "🤩"],
                "concerned": ["💙", "🫂"],
                "playful": ["😄", "😆"],
                "calm": ["😌", "✨"],
            }
            emojis = emoji_map.get(personality.mood, ["😊"])
            response += f" {random.choice(emojis)}"

        # Add catchphrase occasionally
        if (
            personality.friendship_level >= 3
            and personality.catchphrase
            and random.random() < 0.1
        ):
            response += f" {personality.catchphrase}"

        return response

    def _fallback_response(self, context: Dict) -> str:
        """Generate fallback response when LLM is not available"""
        responses = [
            "That's really interesting! Tell me more about that.",
            "I hear you! How are you feeling about it?",
            "That sounds important to you. Want to talk more about it?",
            "Thanks for sharing that with me!",
        ]
        import random

        return random.choice(responses)

    def _handle_crisis(self, safety_result: Dict, user_id: int, db: Session) -> str:
        """Handle crisis situation"""
        # Log safety event
        safety_filter.log_safety_event(db, user_id, safety_result)

        # Get appropriate response
        if "crisis" in safety_result["flags"] or "abuse" in safety_result["flags"]:
            return safety_filter.get_crisis_response()
        elif "bullying" in safety_result["flags"]:
            return safety_filter.get_bullying_response()
        else:
            return safety_filter.get_inappropriate_decline()

    def _store_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        db: Session,
        flagged: bool = False,
    ) -> Message:
        """Store a message in the database"""
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            timestamp=datetime.now(),
            flagged=flagged,
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message

    def _detect_user_mood(self, message: str) -> str:
        """Simple mood detection"""
        message_lower = message.lower()

        if any(word in message_lower for word in ["sad", "upset", "crying", "depressed"]):
            return "sad"
        elif any(word in message_lower for word in ["worried", "nervous", "scared", "anxious"]):
            return "anxious"
        elif any(word in message_lower for word in ["happy", "excited", "great", "awesome"]):
            return "happy"
        elif any(word in message_lower for word in ["angry", "mad", "furious"]):
            return "angry"
        else:
            return "neutral"

    def _calculate_conversation_metrics(self, conversation_id: int, db: Session) -> Dict:
        """Calculate metrics about the conversation"""
        messages = (
            db.query(Message).filter(Message.conversation_id == conversation_id).all()
        )

        user_messages = [m for m in messages if m.role == "user"]

        if not user_messages:
            return {
                "message_count": 0,
                "avg_message_length": 0,
                "user_question_ratio": 0,
                "positive_joke_response": False,
                "casual_language_detected": False,
            }

        avg_length = sum(len(m.content) for m in user_messages) / len(user_messages)
        question_count = sum(1 for m in user_messages if "?" in m.content)
        question_ratio = question_count / len(user_messages)

        # Check for casual language
        all_text = " ".join(m.content.lower() for m in user_messages)
        casual = any(
            word in all_text for word in ["yeah", "cool", "awesome", "lol", "nice"]
        )

        return {
            "message_count": len(messages),
            "avg_message_length": avg_length,
            "user_question_ratio": question_ratio,
            "positive_joke_response": False,  # Would need more sophisticated detection
            "casual_language_detected": casual,
        }


# Global instance
conversation_manager = ConversationManager()
