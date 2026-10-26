"""
Conversation Manager Service
Orchestrates the conversation flow and message processing
"""

from typing import Dict, Optional, List, Tuple
import logging
import random
import re
from collections import deque
from datetime import datetime

from sqlalchemy.orm import Session
from models.user import User
from models.personality import BotPersonality
from models.conversation import Conversation, Message
from models.memory import UserProfile

from services.llm_service import llm_service
from services.llm_setting import llm_setting
from services.safety_filter import safety_filter
from services.bullying_keyword_list import bullying_keyword_list
from services.crisis_keyword_list import crisis_keyword_list
from services import correction_handler, crisis_context, reply_safety
from services.memory_manager import memory_manager
from services.personality_manager import personality_manager
from services.conversation_tracker import conversation_tracker
from services.feature_gates import can_use_catchphrase
from services.personality_drift_calculator import personality_drift_calculator
from services.emoji_quirk_service import emoji_quirk_service
from services.pun_quirk_service import pun_quirk_service
from services.fact_quirk_service import fact_quirk_service
from services.advice_category_detector import advice_category_detector
from services.advice_template_service import advice_template_service
from services.conversation_summary_service import conversation_summary_service
from services.response_engine import response_engine
from services.utterance_parser import utterance_parser
from services.engagement_tracker import engagement_tracker
from services.gibberish_detector import gibberish_detector
from utils.config import settings
from utils.bounded import BoundedDict

# Most replies should not carry a joke, however high the bot's humor
MAX_JOKE_PROBABILITY = 0.5

# Replies to keyboard mashing and random letters (see services/gibberish_detector.py)
GIBBERISH_REPLIES = [
    "Hmm, I didn't quite catch that. What did you mean?",
    "Oops, I think that got a little jumbled! Can you say it another way?",
    "I'm not sure what that means. Can you tell me again?",
]

logger = logging.getLogger("chatbot.conversation_manager")


RECENT_MESSAGES = 3  # earlier messages the safety check reads crisis phrases against
TOPIC_MESSAGES = 5  # messages whose topic generic advice can be about
SENSITIVE_REPLIES = 4  # replies without jokes after a sad message, including its own

ASK_NAME_AGAIN = ["Hi! What's your name?", "Hey there! What's your name?"]

GENERIC_ADVICE = [
    "That sounds tricky. One thing that can help is talking it over with someone you trust, "
    "like a parent or teacher. What do you think might help?",
    "Hmm, that's a tough one. Sometimes it helps to take a deep breath and think about what "
    "would make things a little better. You could also ask a grown-up you trust. What have you tried so far?",
]

# Keyword mood detection, used when the sentence matches no rule (checked in this order)
_MOOD_KEYWORDS = [
    ("sad", re.compile(r"\b(sad(ness|ly)?|upset(ting)?|crying|depressed)\b")),
    ("anxious", re.compile(r"\b(worried|nervous|scared|anxious)\b")),
    ("happy", re.compile(r"\b(happy|excited|great|awesome)\b")),
    ("angry", re.compile(r"\b(angry|mad|madder|maddening|furious)\b")),
]

# Sad news worth asking about at the start of the next conversation
_CHECK_IN_RE = re.compile(
    r"\b(sick|hospital|died|dead|funeral|divorce|sad|cry\w*|cried|miss|lonely|bull(y|ied|ies)|hurt|"
    r"fight\w*|scared)\b", re.IGNORECASE
)

# Words that end the gentle replies after sad news
_CHEERFUL_RE = re.compile(r"\b(laugh\w*|fun|happy|great|awesome|excited|yay|haha\w*|lol)\b", re.IGNORECASE)

# Advice by topic when no advice template matches (checked in order)
GENERIC_ADVICE_BY_TOPIC = [
    (r"\b(called me|calls me|teas\w*|made fun|making fun|laughed at me|names)\b", [
        "You could say, \"Please stop, I don't like that,\" in a strong, calm voice, and then walk away. If it keeps "
        "happening, tell a teacher or a grown-up you trust. You deserve to be treated kindly!",
    ]),
    (r"\b(money|dollars?|save|saving|spend|allowance)\b", [
        "That's a big choice! You could buy something small now and save the rest, or save it all for something "
        "bigger later. What would make you happiest?",
    ]),
    (r"\b(speech|presentation|present|recital|perform\w*|stage|audition|tryouts?)\b", [
        "Lots of people get nervous about that! Try practicing a few times in front of your family or a mirror, "
        "and take slow, deep breaths before you start. You've got this! What part feels scariest?",
    ]),
    (r"\b(friends?|bff|best friend)\b", [
        "That sounds hard. When you're both calm, you could tell your friend how it made you feel. If it keeps "
        "happening, it's okay to spend time with other friends and to talk to a grown-up you trust. What do you think?",
    ]),
    (r"\b(brother|sister|sibling|cousin)\b", [
        "That sounds frustrating! You could calmly tell them how it makes you feel and what you'd like them to do "
        "instead. If it keeps happening, ask your mom or dad to help. What do you think?",
    ]),
    (r"\b(homework|assignment|project|test|quiz|grade|school|study\w*)\b", [
        "Try breaking it into small steps and doing a little at a time, with short breaks in between. A teacher "
        "or a parent can help you make a plan too! What's the hardest part?",
    ]),
]

# "What should I do?", "can you help me", not "What ride should I go on?"
_ASKS_WHAT_TO_DO_RE = re.compile(
    r"\bwhat (should|can|could|do) I do\b|\bwhat\b[^?.!]*\bI (should|can|could) do\b|\bhelp me\b|\badvice\b"
    r"|\btips\b|\bhow (do|can|should) I (deal|handle|stop|fix|tell|get|make|help)\b|\bwhat (should|can|do) I say\b",
    re.IGNORECASE,
)

# "I'm Lily", "im lily", "I am Lily", "call me Lily", "hi I'm Lily"
_NAME_INTRO_RE = re.compile(
    r"^\s*(?:(?:hi|hey|hello)[\s,!.]+)?(?:i'?m|i am|call me)\s+([A-Za-z][A-Za-z'-]{1,19})\s*[.!]*\s*$",
    re.IGNORECASE,
)
# "lol jk im Finn", "just kidding, my name is Finn": a correction, so a lowercase name counts
_NAME_CORRECTION_RE = re.compile(
    r"^\s*(?:(?:lol|haha+|hehe+)[\s,!.]+)?(?:jk|j/k|just kidding|kidding|actually|no wait|wait|not really)"
    r"[\s,!.]+(?:i'?m|i am|call me|my name is|my name's)\s+([A-Za-z][A-Za-z'-]{1,19})\s*[.!]*\s*$",
    re.IGNORECASE,
)

# "no she works there" after a caring reply to "my grandma is in the hospital": the bot read
# something as sad that was not (not "no I don't want to", "no thanks")
_MISREAD_RE = re.compile(
    r"^\s*(?:no+|nope|nah|actually|wait)\b[\s,!.]+"
    r"(?!(?:i\s+)?(?:don'?t|do not|not|never|thanks|thank|way|more|i'?m\s+(?:not|okay|ok|fine))\b)\w+\s+\w+",
    re.IGNORECASE,
)

def _prompt_text(text: str, bot_name: str) -> str:
    """
    The child's text for the model prompt, on one line and without labels that would read
    as a new speaker or instructions ("Buddy: I will...", "INSTRUCTIONS:")
    """
    text = " ".join((text or "").split())
    labels = rf"(?:user|human|assistant|system|instructions?|{re.escape(bot_name)})"
    return re.sub(rf"\b({labels})\s*:", r"\1 -", text, flags=re.IGNORECASE)


_NOT_NAMES = {
    "hi", "hey", "hello", "yo", "sup", "yes", "no", "yeah", "yep", "nope", "ok", "okay", "maybe",
    "fine", "good", "great", "bad", "back", "here", "home", "done", "ready", "sorry", "bored",
    "hungry", "tired", "sleepy", "sick", "busy", "nothing", "not", "so", "very", "really", "just",
    "thanks", "bye", "lol", "idk", "what", "why", "who", "cool", "nice", "fun", "also", "too",
}


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
        # Whether the last reply to each user had a fun fact or pun (no two in a row)
        self._joked_last_reply: Dict[int, bool] = BoundedDict()
        # Users whose last reply asked "What's your name?", so a short answer is their name
        self._awaiting_name: set = set()
        # Replies left with no fun facts or puns, after the child said something sad
        self._sensitive_replies: Dict[int, int] = BoundedDict()
        # The child's last few messages, for reading crisis phrases in context ("beats me"
        # after talking about Mario Kart)
        self._recent_messages: Dict[int, deque] = BoundedDict()
        # A longer window for the topic of generic advice ("what should I say?" a few messages after the teasing)
        self._topic_messages: Dict[int, deque] = BoundedDict()
        # Messages like "my sister always beats me" whose meaning the bot asked about
        self._pending_clarification: Dict[int, str] = BoundedDict()
        # The bot's last reply to each user, for telling a correction ("no its Sammy") from an
        # answer to a yes/no question ("Do you like tacos too?" "no, burgers")
        self._last_reply: Dict[int, str] = BoundedDict()
        # Users whose last message got a caring reply only for its words ("hospital"), with no
        # sad, scared or angry event in its parse: the reading may have been wrong
        self._upset_by_words: set = set()

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
        # Pronouns in a new conversation should not refer to people from the last one
        response_engine.reset_references(user_id)
        # The last reply of the previous conversation is not scored against this one
        engagement_tracker.discard_pending(user_id)
        self.message_count = 0
        self.conversation_start_time = datetime.now()

        # Update user's last active
        user.last_active = datetime.now()
        db.commit()

        # Track conversation start (daily check-in, streaks, points)
        checkin_info = conversation_tracker.on_conversation_start(
            user_id, personality, db, conversation_id=conversation.id
        )

        # Generate greeting based on time since last conversation
        greeting = self._generate_greeting(user, personality, db, conversation.id)
        self._set_awaiting_name(user_id, greeting)
        self._sensitive_replies.pop(user_id, None)
        self._recent_messages.pop(user_id, None)
        self._topic_messages.pop(user_id, None)
        self._pending_clarification.pop(user_id, None)

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
        was_upset_by_words = user_id in self._upset_by_words
        self._upset_by_words.discard(user_id)
        recent = self._recent_messages.setdefault(user_id, deque(maxlen=RECENT_MESSAGES))
        recent_messages = list(recent)
        recent.append(user_message)
        self._topic_messages.setdefault(user_id, deque(maxlen=TOPIC_MESSAGES)).append(user_message)

        # The answer to "Do you mean she wins at games, or that she hits you?". It gets the
        # short game reply only if it raises no safety concern of its own ("no. i want to
        # kill myself" is a crisis, whatever it answers)
        clarified = self._pending_clarification.pop(user_id, None)
        if clarified is not None:
            meaning = crisis_context.clarification_answer(user_message)
            if meaning != "violence" and safety_filter.check_message(user_message)["severity"] != "none":
                clarified = None  # checked as a message of its own below
            elif meaning != "violence":
                response = (crisis_context.CLARIFY_REPLY_GAME if meaning == "game"
                            else crisis_context.CLARIFY_REPLY_UNCLEAR)
                return self._safety_context_reply(conversation_id, user_id, user_message, response, db)

        # 1. Safety check. Bullying and crisis words are checked against who or what the
        # message is about ("she takes my stuff" right after "I have a little sister",
        # "I'm scared of them" about spiders)
        resolved_preview = None
        if (bullying_keyword_list.contains_bullying_keywords(user_message)
                or crisis_keyword_list.contains_crisis_keywords(user_message)):
            try:
                resolved_preview = response_engine.references.preview(user_message, user_id)
            except Exception as e:
                logger.error(f"Error resolving references for the safety check: {e}", exc_info=True)
        if clarified is not None:
            # The child said yes, it means hitting: the original message gets the crisis response
            safety_result = safety_filter.check_message(clarified, user_id=user_id, force_crisis=True)
        else:
            safety_result = safety_filter.check_message(
                user_message, user_id=user_id, resolved_message=resolved_preview,
                recent_messages=recent_messages, known_people=self._known_people(user_id),
            )

        if safety_result["action"] == "clarify":
            self._pending_clarification[user_id] = user_message
            return self._safety_context_reply(
                conversation_id, user_id, user_message, safety_result["response_message"], db
            )
        if safety_result["action"] == "fear_support":
            # "It makes me scared" about a storm or parents arguing: comfort, not a hotline
            self._sensitive_replies[user_id] = SENSITIVE_REPLIES
            return self._safety_context_reply(
                conversation_id, user_id, user_message, safety_result["response_message"], db
            )

        # Crisis, blocked and bullying messages are not engagement signals for the last reply
        if not safety_result["safe"] or safety_result["action"] in ("supportive_response", "crisis_response"):
            engagement_tracker.discard_pending(user_id)

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

            # Gentle replies for the next few messages (no jokes or cheerful emojis)
            self._sensitive_replies[user_id] = SENSITIVE_REPLIES
            # Keep track of who the child is talking about ("she is 14" after "my sister ...")
            self._resolve_references(user_message, user_id)

            # Handle crisis with category-specific response
            response = self._handle_crisis(safety_result, user_id, conversation_id, db)

            # Store the message and response
            user_msg = self._store_message(conversation_id, "user", user_message, db, flagged=True)
            self._store_message(conversation_id, "assistant", response, db)

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

        # Blocked (high severity) or supportive (medium severity) messages get the
        # safety filter's prepared response instead of an LLM-generated one
        if not safety_result["safe"] or safety_result["action"] == "supportive_response":
            response = safety_result.get("response_message") or (
                safety_filter.get_bullying_response()
                if "bullying" in safety_result["flags"]
                else safety_filter.get_inappropriate_decline()
            )

            # Gentle replies for the next few messages (no jokes or cheerful emojis)
            self._sensitive_replies[user_id] = SENSITIVE_REPLIES
            # Keep track of who the child is talking about ("they do it every day")
            self._resolve_references(user_message, user_id)

            user_msg = self._store_message(conversation_id, "user", user_message, db, flagged=True)
            self._store_message(conversation_id, "assistant", response, db)
            self.message_count += 1

            safety_filter.log_safety_event(db, user_id, safety_result, message_id=user_msg.id)

            if safety_result.get("notify_parent", False):
                from services.parent_notification_service import parent_notification_service

                parent_notification_service.notify_high_severity_event(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    safety_result=safety_result,
                    db=db,
                )

            logger.warning(
                f"Safety response used for user {user_id}: "
                f"flags={safety_result['flags']}, severity={safety_result['severity']}"
            )

            return {
                "content": response,
                "metadata": {
                    "safety_flag": True,
                    "severity": safety_result["severity"],
                    "flags": safety_result["flags"],
                    "notify_parent": safety_result.get("notify_parent", False),
                },
            }

        # Keyboard mashing or random letters ("asdfghjkl"): ask what they meant. The message
        # is stored, but not scored for engagement, mined for memories or pronoun references,
        # or counted for friendship points, and it gets no LLM reply or quirks.
        if safety_result["severity"] == "none" and gibberish_detector.is_gibberish(user_message):
            engagement_tracker.discard_pending(user_id)
            response = random.choice(GIBBERISH_REPLIES)
            self._store_message(conversation_id, "user", user_message, db)
            self._store_message(conversation_id, "assistant", response, db)
            self.message_count += 1
            return {
                "content": response,
                "metadata": {"safety_flag": False, "gibberish": True},
            }

        # 2. Store user message
        user_msg = self._store_message(
            conversation_id, "user", user_message, db,
            flagged=safety_result["severity"] != "none",
        )
        self.message_count += 1

        # Log low-severity flags (e.g. mild profanity) that are allowed through
        if safety_result["severity"] != "none":
            safety_filter.log_safety_event(db, user_id, safety_result, message_id=user_msg.id)

        # "no its Sammy", "I didn't say that": the bot got something wrong, so the message is
        # not scored as engagement with its last reply
        if memory_manager.awaiting_correction(user_id):
            correction = correction_handler.answer(user_message)  # "frogs" after "What did you mean?"
            if correction is None:
                memory_manager.forget_retracted(user_id)
        else:
            correction = correction_handler.detect(user_message)
            if (correction and correction.plain_no
                    and correction_handler.asks_yes_no(self._last_reply.get(user_id))):
                correction = None
        if correction and (correction.value or correction.kind != correction_handler.REPLACE):
            engagement_tracker.discard_pending(user_id)

        # Score how engaged this message is and credit the choices in the bot's last reply
        self._record_engagement(user_id, user_message, db)

        # 3. Get personality (needed early for tracking)
        personality = (
            db.query(BotPersonality).filter(BotPersonality.user_id == user_id).first()
        )

        # 4. Track message and award points for activities
        message_tracking = conversation_tracker.on_message_sent(
            user_id, personality, user_message, db
        )

        # Resolve pronouns to earlier people and things ("she" -> "my best friend Maya")
        # for the rule-based analysis; the stored message and the LLM prompt keep the original
        analysis_message = self._resolve_references(
            self._capitalize_known_names(self._name_introduction(user_message, user_id), user_id, db), user_id)

        # 5. Extract and store memories, and change the ones the child corrected
        previous_memories = memory_manager.last_written(user_id)
        memory_manager.extract_and_store_memories(analysis_message, user_id, db)
        corrected = (self._apply_correction(correction, previous_memories, user_id, analysis_message, db)
                     if correction else None)
        awaiting_name = user_id in self._awaiting_name

        # 6. Build context
        context = self._build_context(analysis_message, user_id, personality, db)

        # Something sad ("my grandpa is in the hospital"): a caring emoji, and no jokes,
        # cheerful emojis or "What happened next?" in this reply and the next few
        upset = (context.get("detected_mood") in ("sad", "anxious", "angry")
                 or emoji_quirk_service.is_negative(user_message))
        # "no she works there": the caring reply was a misreading, so the gentle replies stop
        misread = bool(was_upset_by_words and not upset and not corrected and _MISREAD_RE.match(user_message))
        if upset:
            self._sensitive_replies[user_id] = SENSITIVE_REPLIES
            if not self._parsed_mood(analysis_message):
                self._upset_by_words.add(user_id)
        elif misread:
            self._sensitive_replies.pop(user_id, None)
        elif context.get("detected_mood") == "happy" or _CHEERFUL_RE.search(user_message):
            self._sensitive_replies.pop(user_id, None)  # "but then we laughed"
        sensitive = self._sensitive_replies.get(user_id, 0) > 0
        if sensitive:
            self._sensitive_replies[user_id] -= 1
        context["sensitive"] = sensitive
        # Advice from a stored template matching what the child asked about, if any
        context["advice"] = self._template_advice(user_message, context, personality, db)

        # 7. Generate response
        # Use the LLM when turned on (off by default) and loadable; otherwise the rule-based engine.
        # The child's words are only echoed back when the safety filter found nothing.
        allow_reflection = safety_result["severity"] == "none"
        reply_features: Dict[str, str] = {}
        try:
            if corrected:
                # Say what the bot now remembers ("Oops, got it! Your dog is named Rex.")
                raw_response = corrected["reply"]
                reply_features["rule"] = "correction"
            elif llm_setting.enabled() and llm_service.ensure_loaded(timeout=60.0):
                reply_plan = self._plan_llm_reply(context, personality, db)
                prompt = self._build_prompt(context, user_message, personality, reply_plan)
                raw_response = llm_service.generate(prompt, max_tokens=300, temperature=0.7)
                unsafe = self._unsafe_llm_reply(raw_response)
                if unsafe:
                    # The model wrote something the child should not see: the rule-based reply instead
                    logger.warning(f"Model reply not used for user {user_id}: {unsafe}")
                    raw_response = self._rule_based_response(
                        analysis_message, context, personality, allow_reflection, db, reply_features
                    )
                else:
                    reply_features.update(self._observed_llm_features(raw_response, context, reply_plan))
            else:
                if llm_setting.enabled():
                    logger.warning("LLM model not available, using rule-based responses")
                raw_response = self._rule_based_response(
                    analysis_message, context, personality, allow_reflection, db, reply_features
                )
        except Exception as e:
            logger.error(f"Error loading/generating from LLM: {e}")
            reply_features.clear()
            raw_response = self._rule_based_response(
                analysis_message, context, personality, allow_reflection, db, reply_features
            )

        if misread:
            raw_response = "Oh, sorry, I misunderstood! " + re.sub(r"^Oh,\s+(\w)", lambda m: m.group(1).upper(),
                                                                   raw_response)

        # "Hi" after the bot asked the child's name: ask again
        if awaiting_name and reply_features.get("rule") == "greeting":
            raw_response = random.choice(ASK_NAME_AGAIN)
            reply_features["rule"] = "ask_name"

        # 8. Apply personality to response
        final_response = self._apply_personality_filter(
            raw_response, personality, user_message, features=reply_features,
            # A requested joke or fact does not get another one added, and advice gets none
            allow_jokes=not response_engine.rule_flag(reply_features.get("rule"), "no_jokes")
            and not corrected and not context.get("advice") and not sensitive
            and not self._mentions_person(user_id),
            emoji_mood="concerned" if upset else None,
            allow_emojis=upset or not sensitive,
        )
        self._set_awaiting_name(user_id, final_response)

        # 9. Safety check on response (optional)
        response_safety = safety_filter.check_message(final_response)
        if not response_safety["safe"]:
            final_response = (
                "Hmm, I'm not sure how to respond to that. Want to talk about something else?"
            )
            reply_features.clear()

        # Remember this reply's choices; the child's next message will be scored against them
        engagement_tracker.set_pending(user_id, final_response, reply_features, user_message)

        # Let the child refer to what the bot just said ("That's so cool!")
        try:
            response_engine.record_bot_reply(user_id, raw_response, reply_features.get("humor"))
        except Exception as e:
            logger.error(f"Error recording bot reply for references: {e}", exc_info=True)

        # 10. Store assistant response
        self._store_message(conversation_id, "assistant", final_response, db)
        self._last_reply[user_id] = final_response

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

        # The child left after the bot's last reply (unless they had said goodbye)
        try:
            engagement_tracker.record_conversation_end(conversation.user_id, db)
        except Exception as e:
            logger.error(f"Error recording engagement at conversation end: {e}", exc_info=True)
            db.rollback()

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
        self, user: User, personality: BotPersonality, db: Session,
        current_conversation_id: Optional[int] = None,
    ) -> str:
        """
        Greeting based on how long ago the child last talked with the bot: the time since the
        last message of their previous conversation (not the one just started). The first
        conversation gets an introduction.
        """
        previous = (
            db.query(Conversation)
            .filter(Conversation.user_id == user.id, Conversation.id != current_conversation_id)
            .order_by(Conversation.timestamp.desc())
            .first()
        )
        # The child's name, unless it is still the placeholder new accounts get
        name = user.name if user.name and user.name != "User" else None

        if previous is None:
            bot_name = getattr(personality, "name", None) or "Buddy"
            if name:
                return f"Hi {name}! I'm {bot_name}, and I'm so happy to meet you! What do you like to do for fun?"
            return f"Hi there! I'm {bot_name}, your new friend. What's your name?"

        last_message = (
            db.query(Message)
            .filter(Message.conversation_id == previous.id)
            .order_by(Message.timestamp.desc())
            .first()
        )
        last_active = last_message.timestamp if last_message else previous.timestamp
        hours_since = (datetime.now() - last_active).total_seconds() / 3600
        name = name or "there"

        # Last time the child talked about something sad ("my grandma is sick"): check in
        child_messages = (
            db.query(Message)
            .filter(Message.conversation_id == previous.id, Message.role == "user")
            .order_by(Message.timestamp.desc())
            .limit(5)
            .all()
        )
        if any(_CHECK_IN_RE.search(m.content or "") for m in child_messages):
            return f"Hi {name}! I've been thinking about you. Last time things seemed a little hard. How are you feeling today?"

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

        # Everything the child has told the bot, by key ("favorite_color": "purple"), so it
        # can answer "What's my favorite color?" and "Do you remember my dog?"; with categories
        # too ("person": a pet's or person's name), for "What pets do I have?"
        try:
            rows = db.query(UserProfile).filter(UserProfile.user_id == user_id).all()
            known_facts = {m.key: m.value for m in rows}
            known_memories = [(m.category, m.key, m.value) for m in rows]
        except Exception as e:
            logger.error(f"Error loading memories: {e}", exc_info=True)
            known_facts, known_memories = {}, []

        return {
            "personality": personality,
            "keywords": keywords,
            "relevant_memories": memories,
            "known_facts": known_facts,
            "known_memories": known_memories,
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

    def _plan_llm_reply(self, context: Dict, personality: BotPersonality, db: Session) -> Dict[str, bool]:
        """
        Decide the optional parts of an LLM reply the same way the rule-based engine does:
        from the personality at first, then from what this child engages with
        """
        policy = engagement_tracker.policy(personality.user_id, db)
        plan = {"follow_up": policy.decide("follow_up", personality.curiosity)}
        if personality.friendship_level >= 3 and context.get("relevant_memories"):
            plan["callback"] = policy.decide("callback", 0.35)
        return plan

    @staticmethod
    def _observed_llm_features(reply: str, context: Dict, plan: Dict[str, bool]) -> Dict[str, str]:
        """
        What the LLM reply actually did, for engagement learning. The model may not follow
        the plan's instructions, so the reply itself is checked.
        """
        features = {"rule": "llm", "follow_up": "yes" if reply.rstrip().endswith("?") else "no"}
        if "callback" in plan:
            reply_lower = reply.lower()
            mentioned = any(str(getattr(m, "value", "")).lower() in reply_lower
                            for m in context.get("relevant_memories", []) if getattr(m, "value", None))
            features["callback"] = "yes" if mentioned else "no"
        return features

    def _build_prompt(
        self,
        context: Dict,
        user_message: str,
        personality: BotPersonality,
        reply_plan: Optional[Dict[str, bool]] = None,
    ) -> str:
        """Build LLM prompt with personality and context"""
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
        advice_text = context.get("advice")
        if advice_text:
            system += (
                "\nADVICE TO GIVE (from a reviewed advice template; use its ideas in your own "
                "words and keep to the length below):\n" + advice_text + "\n"
            )

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
        # Choices learned from what this child engages with
        reply_plan = reply_plan or {}
        if "follow_up" in reply_plan:
            system += ("- End with one short question about what they said\n" if reply_plan["follow_up"]
                       else "- Do not ask a question this time; just respond warmly\n")
        if reply_plan.get("callback"):
            system += "- Briefly mention one thing you remember about them\n"

        # Build conversation history
        history = ""
        for msg in context.get("recent_messages", [])[-6:]:
            role_name = "User" if msg.role == "user" else personality.name
            history += f"{role_name}: {_prompt_text(msg.content, personality.name)}\n"

        # Full prompt
        prompt = f"{system}\n\n{history}User: {_prompt_text(user_message, personality.name)}\n{personality.name}:"

        return prompt

    def _apply_personality_filter(
        self,
        response: str,
        personality: BotPersonality,
        context: str = "",
        features: Optional[Dict[str, str]] = None,
        allow_jokes: bool = True,
        emoji_mood: Optional[str] = None,
        allow_emojis: bool = True,
    ) -> str:
        """
        Apply personality quirks to response

        A fact or pun is only added to a reply that does not ask the child something (a
        question or "Tell me more!" should follow what the child said, not a joke), never to two replies in a
        row, and after any emojis so an emoji cannot land between a joke's setup and
        punchline. A reply gets at most one. The catchphrase goes before a closing question.

        If features is given, records whether a fun fact or pun was added ("humor" =
        "fact", "pun" or "none") so the child's reaction can be credited to it.
        emoji_mood overrides the bot's mood for choosing emojis ("concerned" for caring ones);
        allow_emojis=False leaves them out.
        """
        quirks = personality.get_quirks()
        user_id = getattr(personality, "user_id", None)
        # Higher humor means more puns and facts (0.5x at humor 0.0, 1.5x at humor 1.0)
        humor = getattr(personality, "humor", 0.5)
        humor_scale = 0.5 + humor if isinstance(humor, (int, float)) else 1.0

        joke_allowed = (bool(response) and allow_jokes and not self._invites_answer(response)
                        and not self._joked_last_reply.get(user_id, False))

        # At most one fact or pun per reply (shares_facts / tells_puns quirks)
        joke = self._choose_joke(quirks, personality, humor_scale) if joke_allowed else None
        self._joked_last_reply[user_id] = joke is not None
        if features is not None and joke_allowed and ("shares_facts" in quirks or "tells_puns" in quirks):
            features["humor"] = joke or "none"

        # Apply uses_emojis quirk with enhanced emoji service
        if "uses_emojis" in quirks and allow_emojis:
            # Intensity varies by friendship level
            # Higher friendship = more emojis
            base_intensity = 0.4
            level_bonus = (personality.friendship_level - 1) * 0.05
            intensity = min(0.7, base_intensity + level_bonus)

            response = emoji_quirk_service.apply_emojis(
                response, mood=emoji_mood or personality.mood, intensity=intensity
            )

        # The fact or pun goes at the end, after the emojis
        if joke == "fact":
            response = fact_quirk_service.add_fact(response, context=context, probability=1.0)
        elif joke == "pun":
            response = pun_quirk_service.add_pun(response, context=context, probability=1.0)

        # Add catchphrase occasionally (if feature unlocked), before any closing question
        if (
            can_use_catchphrase(personality)
            and personality.catchphrase
            and random.random() < 0.1
        ):
            body, closing_question = self._split_closing_question(response)
            response = " ".join(p for p in (body, personality.catchphrase, closing_question) if p)

        return re.sub(r" {2,}", " ", response)

    def _invites_answer(self, text: str) -> bool:
        """
        True if the reply ends by asking the child something: a question, or a closing
        "Tell me ..." ("Tell me more!")
        """
        body, closing_question = self._split_closing_question(text)
        if closing_question:
            return True
        sentences = [s for s in re.split(r"(?<=[.!?])\s+", body.strip()) if any(c.isalpha() for c in s)]
        return bool(sentences) and sentences[-1].lower().startswith("tell me")

    @staticmethod
    def _choose_joke(quirks: List[str], personality: BotPersonality, humor_scale: float) -> Optional[str]:
        """
        Whether this reply gets a fun fact or a pun (never both). Each quirk has its own
        chance (rising with friendship level and humor); one roll uses their combined chance,
        capped at MAX_JOKE_PROBABILITY, then picks which one in proportion to the chances.
        """
        level_bonus = (personality.friendship_level - 1) * 0.02
        chances = {}
        if "shares_facts" in quirks:
            chances["fact"] = min(0.35, 0.20 + level_bonus) * humor_scale
        if "tells_puns" in quirks:
            chances["pun"] = min(0.40, 0.25 + level_bonus) * humor_scale
        if not chances:
            return None

        none_chance = 1.0
        for chance in chances.values():
            none_chance *= 1.0 - min(chance, 1.0)
        if random.random() >= min(1.0 - none_chance, MAX_JOKE_PROBABILITY):
            return None
        return random.choices(list(chances), weights=list(chances.values()))[0]

    @staticmethod
    def _split_closing_question(text: str) -> Tuple[str, str]:
        """
        Split a reply into (body, closing question). The closing question is the run of
        sentences at the end that are questions; emoji-only fragments stay with the
        sentence before them. ("Cool! What's yours? 😄" -> ("Cool!", "What's yours? 😄"))
        """
        sentences = []
        for part in re.split(r"(?<=[.!?])\s+", text.strip()):
            if sentences and not re.search(r"\w", part):
                sentences[-1] = f"{sentences[-1]} {part}"
            elif part:
                sentences.append(part)

        split = len(sentences)
        while split > 0 and re.search(r"\?\W*$", sentences[split - 1]):
            split -= 1
        return " ".join(sentences[:split]), " ".join(sentences[split:])

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

    def _safety_context_reply(
        self, conversation_id: int, user_id: int, user_message: str, response: str, db: Session
    ) -> Dict:
        """
        Store and return a reply the safety check chose after reading a crisis phrase in
        context (a clarification question, comfort for a fear, or the answer to a question)
        """
        self._resolve_references(user_message, user_id)
        engagement_tracker.discard_pending(user_id)
        self._store_message(conversation_id, "user", user_message, db)
        self._store_message(conversation_id, "assistant", response, db)
        self.message_count += 1
        self._set_awaiting_name(user_id, response)
        return {"content": response, "metadata": {"safety_flag": False}}

    @staticmethod
    def _capitalize_known_names(message: str, user_id: int, db: Session) -> str:
        """
        "max learned a new trick" -> "Max learned a new trick", for people and pets the child
        named before. A name that is also a word ("star") is capitalized only where it starts
        a sentence, so "I saw a star" stays.
        """
        try:
            names = [m.value for m in db.query(UserProfile).filter(
                UserProfile.user_id == user_id, UserProfile.category == "person").all()]
        except Exception:
            return message
        words = utterance_parser.known_words()
        for name in names:
            if not name or not name.isalpha() or not name[0].isupper():
                continue
            lower = re.escape(name.lower())
            if name.lower() in words:
                pattern = rf"(^|[.!?]\s+)({lower})\b"
                message = re.sub(pattern, lambda m: m.group(1) + name, message)
            else:
                message = re.sub(rf"\b{lower}\b", name, message)
        return message

    @staticmethod
    def _mentions_person(user_id: int) -> bool:
        """
        True if the child's latest message was about someone ("my teacher is Mrs Brown"):
        news about people gets a reply about them, not a joke or fun fact added on
        """
        try:
            state = response_engine.references.state(user_id)
            return any(p.turn == state.turn for p in state.people)
        except Exception:
            return False

    @staticmethod
    def _known_people(user_id: int) -> List[str]:
        """Names of people the child mentioned recently"""
        try:
            return [p.name for p in response_engine.references.state(user_id).people if p.name]
        except Exception:
            return []

    def _resolve_references(self, user_message: str, user_id: int) -> str:
        """Resolve pronouns with the rule-based engine's reference tracker, if available"""
        try:
            return response_engine.resolve_references(user_message, user_id)
        except Exception as e:
            logger.error(f"Error resolving references: {e}", exc_info=True)
            return user_message

    @staticmethod
    def _apply_correction(correction, previous_memories: List[Dict], user_id: int, message: str,
                          db: Session) -> Optional[Dict]:
        """
        Change the memories a correction is about (see MemoryManager.apply_correction), and
        the name of a pet or person the child is talking about ("oops his name is Rex")
        """
        try:
            corrected = memory_manager.apply_correction(user_id, correction, previous_memories, db, message)
        except Exception as e:
            logger.error(f"Error applying a correction: {e}", exc_info=True)
            db.rollback()
            return None
        if corrected and corrected.get("renamed"):
            old, new = corrected["renamed"]
            for person in response_engine.references.state(user_id).people:
                if person.name and person.name.lower() == old.lower():
                    person.name = new
        return corrected

    @staticmethod
    def _unsafe_llm_reply(reply: str) -> Optional[str]:
        """
        Why a model reply should not be sent: harmful advice (services/reply_safety.py), or
        what the safety filter blocks or flags as inappropriate, profane or about strangers
        """
        reason = reply_safety.unsafe_reason(reply)
        if reason:
            return reason
        check = safety_filter.check_message(reply)
        if check["severity"] in ("high", "critical") or \
                set(check["flags"]) & {"inappropriate_request", "profanity", "stranger_danger"}:
            return f"safety filter: {', '.join(check['flags']) or check['severity']}"
        return None

    @staticmethod
    def _parsed_mood(message: str) -> Optional[str]:
        """The mood of an event in the message's parse ("my dog died": sad), if any"""
        if not response_engine.is_available():
            return None
        try:
            return response_engine.detect_mood(message)
        except Exception as e:
            logger.error(f"Error detecting mood from parse: {e}")
            return None

    def _record_engagement(self, user_id: int, user_message: str, db: Session) -> None:
        """Score the child's message against the bot's previous reply (never blocks a reply)"""
        try:
            engagement_tracker.record_response(user_id, user_message, db)
        except Exception as e:
            logger.error(f"Error recording engagement: {e}", exc_info=True)
            db.rollback()

    def _rule_based_response(
        self,
        user_message: str,
        context: Dict,
        personality: Optional[BotPersonality],
        allow_reflection: bool,
        db: Optional[Session] = None,
        features: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Generate a reply with the rule-based response engine, or a canned fallback.
        The engine's choices are steered by the child's engagement history and recorded in
        features. Advice from a matching template (context["advice"]) is used as the reply.
        """
        advice = context.get("advice")
        if advice:
            if features is not None:
                features["rule"] = "advice"
            return advice
        try:
            if personality is not None and response_engine.is_available():
                user = getattr(personality, "user", None)
                response = response_engine.generate_response(
                    user_message,
                    personality,
                    context,
                    # New accounts are named "User" until the child says their name
                    user_name=user.name if user is not None and user.name != "User" else None,
                    allow_reflection=allow_reflection,
                    policy=engagement_tracker.policy(personality.user_id, db),
                    features=features,
                )
                # "What should I do?" with no advice template for it: not "What do you think?"
                detection = context.get("advice_request") or {}
                # "Can you give me advice?" after "I have to give a speech and I'm scared"
                asked_after_topic = (features is not None and features.get("rule") == "ask_for_advice"
                                     and len(self._recent_messages.get(personality.user_id, [])) >= 2)
                if (response and features is not None and asked_after_topic) or (
                        response and features is not None and features.get("rule") in ("fallback_question", "should_i")
                        and detection.get("is_advice_request") and _ASKS_WHAT_TO_DO_RE.search(user_message)):
                    features["rule"] = "advice_generic"
                    return self._generic_advice(user_message, personality.user_id)
                if response:
                    return response
        except Exception as e:
            logger.error(f"Error generating rule-based response: {e}", exc_info=True)
        return self._fallback_response(context)

    def _generic_advice(self, user_message: str, user_id: int) -> str:
        """
        Short advice for the topic of the last two messages, or else of the last few, when no
        advice template matches
        """
        recent = list(self._topic_messages.get(user_id, [])) or [user_message]
        for window in (recent[-2:], recent):
            text = " ".join(window).lower()
            for pattern, replies in GENERIC_ADVICE_BY_TOPIC:
                if re.search(pattern, text):
                    return random.choice(replies)
        return random.choice(GENERIC_ADVICE)

    def _set_awaiting_name(self, user_id: int, reply: str) -> None:
        """Remember whether this reply asked the child's name"""
        if "What's your name?" in reply:
            self._awaiting_name.add(user_id)
        else:
            self._awaiting_name.discard(user_id)

    def _name_introduction(self, message: str, user_id: int) -> str:
        """
        "im Lily" / "I'm Lily" -> "My name is Lily." (the parser takes "Lily" for an adverb
        or adjective). Only a capitalized word counts, unless the bot just asked the child's
        name; then a lowercase word, or the name on its own ("lily"), counts too.
        """
        awaiting = user_id in self._awaiting_name
        match = _NAME_INTRO_RE.match(message)
        correction = _NAME_CORRECTION_RE.match(message)
        if correction:
            name = correction.group(1)
        elif match:
            name = match.group(1)
            if not awaiting and not name[0].isupper():
                return message
        elif awaiting and re.fullmatch(r"\s*(?:it'?s\s+|it is\s+)?[A-Za-z][A-Za-z'-]{1,19}\s*[.!]*\s*", message,
                                       re.IGNORECASE):
            # "lily", "it's Lily"
            name = re.sub(r"^\s*(?:it'?s|it is)\s+", "", message, flags=re.IGNORECASE).strip(" .!")
        else:
            return message
        # "hii" is a greeting; "SAM" is Sam
        if name.lower() in self._not_names() or utterance_parser.normalize(name).lower() in self._not_names():
            return message
        if name.isupper():
            name = name.capitalize()
        return f"My name is {name[:1].upper()}{name[1:]}."

    @staticmethod
    def _not_names() -> set:
        """Words that follow "I'm" without being a name ("I'm sad", "I'm bored", "hi")"""
        kb = response_engine.kb if response_engine.is_available() else {}
        words = set(_NOT_NAMES)
        words.update(kb.get("emotions", {}).keys())
        words.update(kb.get("evaluations", {}).keys())
        return words

    def _template_advice(
        self,
        user_message: str,
        context: Dict,
        personality: Optional[BotPersonality],
        db: Session,
    ) -> Optional[str]:
        """
        Personalized advice from the stored templates when the message asks for advice and a
        template available at this friendship level and age matches what it is about
        (see advice_template_service.find_relevant_template); otherwise None
        """
        detection = context.get("advice_request") or {}
        if personality is None or not detection.get("is_advice_request"):
            return None
        # "What should I do?" right after "My friend is being mean to me": the topic is in
        # the message before
        recent = list(self._recent_messages.get(personality.user_id, []))
        if not detection.get("categories") and len(recent) >= 2:
            combined = f"{recent[-2]} {user_message}"
            combined_detection = advice_category_detector.detect_advice_request(combined)
            if combined_detection.get("categories"):
                detection, user_message = combined_detection, combined
        try:
            user = getattr(personality, "user", None)
            return advice_template_service.get_advice_for_context(
                db=db,
                advice_detection=detection,
                personality=personality,
                user_id=personality.user_id,
                user_message=user_message,
                user_age=getattr(user, "age", None),
                detected_mood=context.get("detected_mood"),
            )
        except Exception as e:
            logger.error(f"Error getting template advice: {e}", exc_info=True)
            return None

    def _detect_user_mood(self, message: str) -> str:
        """Detect mood from sentence structure if available, otherwise from keywords"""
        if response_engine.is_available():
            try:
                mood = response_engine.detect_mood(message)
                if mood:
                    return mood
            except Exception as e:
                logger.error(f"Error detecting mood from parse: {e}")

        # Words that are not negated ("I wasn't scared"), with their forms ("upsetting",
        # "maddening") but not other words that start the same ("made")
        tokens = re.findall(r"[a-z']+", message.lower())
        words = " ".join(word for i, word in enumerate(tokens)
                         if not (i > 0 and (tokens[i - 1] in ("not", "no", "never")
                                            or tokens[i - 1].endswith(("n't", "nt")))))

        for mood, pattern in _MOOD_KEYWORDS:
            if pattern.search(words):
                return mood
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
