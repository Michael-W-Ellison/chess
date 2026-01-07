"""
Conversation Manager Service
Orchestrates the conversation flow and message processing
"""

from typing import Dict, Optional, List
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
from services.conversation_tracker import conversation_tracker
from services.feature_gates import can_use_catchphrase, apply_feature_modifiers
from services.personality_drift_calculator import personality_drift_calculator
from services.emoji_quirk_service import emoji_quirk_service
from services.pun_quirk_service import pun_quirk_service
from services.fact_quirk_service import fact_quirk_service
from services.advice_category_detector import advice_category_detector
from services.conversation_summary_service import conversation_summary_service
from utils.config import settings

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

        # Track conversation start (daily check-in, streaks, points)
        checkin_info = conversation_tracker.on_conversation_start(user_id, personality, db)

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
                "friendship_points": personality.friendship_points,
            },
            "checkin_info": checkin_info,
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
        safety_result = safety_filter.check_message(user_message, user_id=user_id)

        if safety_result["severity"] == "critical":
            # Get personality to update mood
            personality = (
                db.query(BotPersonality).filter(BotPersonality.user_id == user_id).first()
            )

            # Change bot's mood to 'concerned' during crisis
            if personality:
                old_mood = personality.mood
                personality.mood = "concerned"
                db.commit()
                logger.info(
                    f"Bot mood changed from '{old_mood}' to 'concerned' due to crisis "
                    f"(user {user_id})"
                )

            # Handle crisis with category-specific response
            response = self._handle_crisis(safety_result, user_id, conversation_id, db)

            # Store the message and response
            user_msg = self._store_message(conversation_id, "user", user_message, db, flagged=True)
            bot_msg = self._store_message(conversation_id, "assistant", response, db)

            # Log safety event with message ID
            safety_filter.log_safety_event(db, user_id, safety_result, message_id=user_msg.id)

            return {
                "content": response,
                "metadata": {
                    "safety_flag": True,
                    "severity": "critical",
                    "crisis_response": True,
                    "flags": safety_result["flags"],
                    "notify_parent": safety_result["notify_parent"],
                    "mood_change": "concerned",
                },
            }

        # 2. Store user message
        user_msg = self._store_message(conversation_id, "user", user_message, db)
        self.message_count += 1

        # 3. Get personality (needed early for tracking)
        personality = (
            db.query(BotPersonality).filter(BotPersonality.user_id == user_id).first()
        )

        # 4. Track message and award points for activities
        message_tracking = conversation_tracker.on_message_sent(
            user_id, personality, user_message, db
        )

        # 5. Extract and store memories
        memory_manager.extract_and_store_memories(user_message, user_id, db)

        # 6. Build context
        context = self._build_context(user_message, user_id, personality, db)

        # 7. Generate response
        # Try to ensure model is loaded (lazy loading)
        try:
            if llm_service.ensure_loaded(timeout=60.0):
                prompt = self._build_prompt(context, user_message, personality)
                # Custom stop sequences to prevent model from generating both sides of conversation
                stop_sequences = [
                    "\nUser:",
                    "\nuser:",
                    "\n\nUser:",
                    f"\n{personality.name}:",
                    "<|endoftext|>",
                    "<|end|>",
                ]
                raw_response = llm_service.generate(
                    prompt,
                    max_tokens=150,
                    temperature=0.7,
                    stop=stop_sequences
                )
            else:
                logger.warning("LLM model not available, using fallback response")
                raw_response = self._fallback_response(context)
        except Exception as e:
            logger.error(f"Error loading/generating from LLM: {e}")
            raw_response = self._fallback_response(context)

        # 8. Apply personality to response
        final_response = self._apply_personality_filter(raw_response, personality, user_message)

        # 9. Safety check on response (optional)
        response_safety = safety_filter.check_message(final_response)
        if not response_safety["safe"]:
            final_response = (
                "Hmm, I'm not sure how to respond to that. Want to talk about something else?"
            )

        # 10. Store assistant response
        self._store_message(conversation_id, "assistant", final_response, db)

        # 11. Update conversation count
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
                "points_awarded": message_tracking.get("points_awarded", []),
                "activities_detected": message_tracking.get("activities_detected", []),
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

        # Generate conversation summary using LLM (if enabled and messages exist)
        if settings.AUTO_GENERATE_SUMMARIES and conversation.messages:
            try:
                logger.info(f"Generating LLM summary for conversation {conversation_id}")
                summary_data = conversation_summary_service.generate_summary(
                    conversation_id, db
                )
                logger.info(
                    f"Summary generated - Topics: {summary_data.get('topics', [])}, "
                    f"Mood: {summary_data.get('mood', 'unknown')}"
                )
            except Exception as e:
                # Don't block conversation end if summary fails
                logger.error(f"Failed to generate summary for conversation {conversation_id}: {e}")
                # Fallback to simple summary
                messages = (
                    db.query(Message)
                    .filter(Message.conversation_id == conversation_id, Message.role == "user")
                    .all()
                )
                if messages:
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
            # Track conversation end (awards points based on quality)
            end_info = conversation_tracker.on_conversation_end(
                conversation_id, personality, db
            )

            # Calculate conversation metrics
            metrics = self._calculate_conversation_metrics(conversation_id, db)

            # Update traits based on conversation
            personality_manager.update_personality_traits(personality, metrics, db)

            # Calculate and apply personality drift based on conversation patterns
            drift_events = personality_drift_calculator.calculate_drift_after_conversation(
                personality, conversation, db
            )

            logger.info(
                f"Conversation ended - Quality: {end_info.get('conversation_quality')}, "
                f"Friendship: Level {personality.friendship_level}, "
                f"Points: {personality.friendship_points}, "
                f"Drift events: {len(drift_events)}"
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
        """Build conversation context with short-term memory from last 3 conversations"""
        # Extract keywords from user message
        keywords = memory_manager.extract_keywords(user_message)

        # Get relevant memories
        memories = memory_manager.get_relevant_memories(user_id, keywords, db, limit=5)

        # Get recent messages from last 3 conversations (short-term memory)
        recent_messages = self._get_short_term_memory(user_id, db)

        # Detect user mood (simple)
        detected_mood = self._detect_user_mood(user_message)

        # Detect advice request and category
        advice_detection = advice_category_detector.detect_advice_request(user_message)

        return {
            "personality": personality,
            "keywords": keywords,
            "relevant_memories": memories,
            "recent_messages": recent_messages,
            "detected_mood": detected_mood,
            "advice_request": advice_detection,
        }

    def _get_short_term_memory(self, user_id: int, db: Session) -> List[Message]:
        """
        Get messages from the last 3 conversations for short-term memory context

        Args:
            user_id: User ID
            db: Database session

        Returns:
            List of messages from last 3 conversations in chronological order
        """
        # Get the last 3 conversations for this user
        last_3_conversations = (
            db.query(Conversation)
            .filter(Conversation.user_id == user_id)
            .order_by(Conversation.timestamp.desc())
            .limit(3)
            .all()
        )

        if not last_3_conversations:
            return []

        # Get conversation IDs
        conversation_ids = [conv.id for conv in last_3_conversations]

        # Get messages from these conversations
        # Limit to ~5 messages per conversation (15 total max)
        messages_per_conversation = 5
        all_messages = []

        for conv_id in reversed(conversation_ids):  # Oldest to newest conversation
            messages = (
                db.query(Message)
                .filter(Message.conversation_id == conv_id)
                .order_by(Message.timestamp.desc())
                .limit(messages_per_conversation)
                .all()
            )
            messages.reverse()  # Chronological order within conversation
            all_messages.extend(messages)

        return all_messages

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

        # Add advice request context if detected
        advice_request = context.get("advice_request", {})
        if advice_request.get("is_advice_request"):
            category = advice_request.get("category", "general")
            category_desc = advice_category_detector.get_category_description(category)
            system += f"\n\nADVICE REQUEST DETECTED:\n"
            system += f"- Category: {category}\n"
            system += f"- Type: {category_desc}\n"
            system += f"- The user is asking for your advice and guidance on this topic.\n"
            system += f"- Provide supportive, age-appropriate advice.\n"

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
        self, response: str, personality: BotPersonality, context: str = ""
    ) -> str:
        """Apply personality quirks to response"""
        import random

        quirks = personality.get_quirks()

        # Apply shares_facts quirk
        if "shares_facts" in quirks:
            # Probability increases slightly with friendship level
            base_probability = 0.20
            level_bonus = (personality.friendship_level - 1) * 0.02
            probability = min(0.35, base_probability + level_bonus)

            response = fact_quirk_service.add_fact(
                response, context=context, probability=probability
            )

        # Apply tells_puns quirk
        if "tells_puns" in quirks:
            # Probability increases slightly with friendship level
            base_probability = 0.25
            level_bonus = (personality.friendship_level - 1) * 0.02
            probability = min(0.40, base_probability + level_bonus)

            response = pun_quirk_service.add_pun(
                response, context=context, probability=probability
            )

        # Apply uses_emojis quirk with enhanced emoji service
        if "uses_emojis" in quirks:
            # Intensity varies by friendship level
            # Higher friendship = more emojis
            base_intensity = 0.4
            level_bonus = (personality.friendship_level - 1) * 0.05
            intensity = min(0.7, base_intensity + level_bonus)

            response = emoji_quirk_service.apply_emojis(
                response, mood=personality.mood, intensity=intensity
            )

        # Add catchphrase occasionally (if feature unlocked)
        if (
            can_use_catchphrase(personality)
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

    def _handle_crisis(
        self, safety_result: Dict, user_id: int, conversation_id: int, db: Session
    ) -> str:
        """
        Handle crisis situation with category-specific response

        Args:
            safety_result: Result from safety_filter.check_message()
            user_id: User ID
            conversation_id: Current conversation ID
            db: Database session

        Returns:
            Crisis response message
        """
        # Use the response_message from safety_result which is category-specific
        response = safety_result.get("response_message", "")

        # If no response in result, get default crisis response
        if not response:
            if "crisis" in safety_result["flags"] or "abuse" in safety_result["flags"]:
                response = safety_filter.get_crisis_response()
            elif "bullying" in safety_result["flags"]:
                response = safety_filter.get_bullying_response()
            else:
                response = safety_filter.get_inappropriate_decline()

        # Trigger parent notification if needed
        if safety_result.get("notify_parent", False):
            self._notify_parent_of_crisis(
                user_id=user_id,
                conversation_id=conversation_id,
                safety_result=safety_result,
                db=db
            )

        logger.warning(
            f"Crisis detected for user {user_id}: "
            f"flags={safety_result['flags']}, severity={safety_result['severity']}"
        )

        return response

    def _notify_parent_of_crisis(
        self,
        user_id: int,
        conversation_id: int,
        safety_result: Dict,
        db: Session
    ) -> None:
        """
        Notify parent about crisis event

        Args:
            user_id: User ID
            conversation_id: Conversation ID
            safety_result: Safety check result
            db: Database session
        """
        # Import here to avoid circular dependency
        from services.parent_notification_service import parent_notification_service

        # Send parent notification
        parent_notification_service.notify_crisis_event(
            user_id=user_id,
            conversation_id=conversation_id,
            safety_result=safety_result,
            db=db
        )

        logger.info(
            f"Parent notification triggered for user {user_id}: "
            f"severity={safety_result['severity']}, flags={safety_result['flags']}"
        )

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
