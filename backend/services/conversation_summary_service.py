"""
Conversation Summary Service
Generates summaries of conversations using LLM for parent review
"""

from typing import Optional, Dict, List
from datetime import datetime
from sqlalchemy.orm import Session
import logging

from models.conversation import Conversation, Message
from services.llm_service import llm_service

logger = logging.getLogger("chatbot.conversation_summary")


class ConversationSummaryService:
    """
    Service for generating conversation summaries using LLM

    Analyzes conversation messages and generates:
    - Overall summary of topics discussed
    - Key concerns or notable moments
    - Mood assessment
    - Topics list
    """

    def __init__(self):
        self.llm = llm_service

    def generate_summary(self, conversation_id: int, db: Session) -> Dict[str, any]:
        """
        Generate a summary for a conversation using LLM

        Args:
            conversation_id: ID of the conversation to summarize
            db: Database session

        Returns:
            Dictionary containing:
                - summary: Text summary of the conversation
                - topics: List of topics discussed
                - mood: Overall mood detected
                - key_moments: List of important exchanges
                - safety_concerns: Any safety issues detected
        """
        # Fetch conversation with messages
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        if not conversation.messages:
            return {
                "summary": "No messages in this conversation.",
                "topics": [],
                "mood": "neutral",
                "key_moments": [],
                "safety_concerns": []
            }

        # Build conversation text
        conversation_text = self._build_conversation_text(conversation.messages)

        # Generate summary using LLM
        summary_data = self._generate_llm_summary(conversation_text)

        # Update conversation record
        conversation.conversation_summary = summary_data["summary"]
        conversation.mood_detected = summary_data["mood"]
        conversation.set_topics(summary_data["topics"])
        conversation.message_count = len(conversation.messages)

        # Calculate duration if timestamps available
        if len(conversation.messages) >= 2:
            first_msg = conversation.messages[0]
            last_msg = conversation.messages[-1]
            duration = (last_msg.timestamp - first_msg.timestamp).total_seconds()
            conversation.duration_seconds = int(duration)

        db.commit()

        logger.info(f"Generated summary for conversation {conversation_id}")

        return summary_data

    def generate_batch_summaries(
        self,
        conversation_ids: List[int],
        db: Session
    ) -> Dict[int, Dict[str, any]]:
        """
        Generate summaries for multiple conversations

        Args:
            conversation_ids: List of conversation IDs
            db: Database session

        Returns:
            Dictionary mapping conversation IDs to their summaries
        """
        results = {}

        for conv_id in conversation_ids:
            try:
                results[conv_id] = self.generate_summary(conv_id, db)
            except Exception as e:
                logger.error(f"Failed to generate summary for conversation {conv_id}: {e}")
                results[conv_id] = {
                    "error": str(e),
                    "summary": "Failed to generate summary",
                    "topics": [],
                    "mood": "unknown",
                    "key_moments": [],
                    "safety_concerns": []
                }

        return results

    def get_summary(self, conversation_id: int, db: Session) -> Optional[str]:
        """
        Get existing summary for a conversation

        Args:
            conversation_id: ID of the conversation
            db: Database session

        Returns:
            Summary text or None if not available
        """
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

        if conversation:
            return conversation.conversation_summary

        return None

    def _build_conversation_text(self, messages: List[Message]) -> str:
        """
        Build formatted conversation text from messages

        Args:
            messages: List of Message objects

        Returns:
            Formatted conversation string
        """
        lines = []

        for msg in messages:
            role_name = "Child" if msg.role == "user" else "Assistant"
            lines.append(f"{role_name}: {msg.content}")

        return "\n\n".join(lines)

    def _generate_llm_summary(self, conversation_text: str) -> Dict[str, any]:
        """
        Use LLM to generate conversation summary

        Args:
            conversation_text: Formatted conversation text

        Returns:
            Dictionary with summary, topics, mood, etc.
        """
        # Check if model is loaded
        if not self.llm.is_loaded:
            logger.warning("LLM not loaded, using fallback summary generation")
            return self._fallback_summary(conversation_text)

        # Build summarization prompt
        prompt = self._build_summary_prompt(conversation_text)

        try:
            # Generate summary with LLM
            response = self.llm.generate(
                prompt=prompt,
                max_tokens=400,
                temperature=0.3,  # Lower temperature for more factual summaries
                stop=["\n\n---", "END_SUMMARY"]
            )

            # Parse LLM response
            summary_data = self._parse_llm_response(response, conversation_text)

            return summary_data

        except Exception as e:
            logger.error(f"LLM summary generation failed: {e}")
            return self._fallback_summary(conversation_text)

    def _build_summary_prompt(self, conversation_text: str) -> str:
        """
        Build prompt for LLM summarization

        Args:
            conversation_text: The conversation to summarize

        Returns:
            Formatted prompt string
        """
        prompt = f"""You are analyzing a conversation between a child and a chess tutoring assistant. Your task is to create a helpful summary for the child's parent.

CONVERSATION:
{conversation_text}

Please provide a concise summary following this format:

SUMMARY: [2-3 sentences describing what was discussed]

TOPICS: [Comma-separated list of main topics, e.g., "opening strategies, pawn structure, endgame tactics"]

MOOD: [One word: positive, neutral, frustrated, confused, engaged, or discouraged]

KEY_MOMENTS: [1-2 notable exchanges or learning moments]

SAFETY_CONCERNS: [Any concerning content, or "None"]

Now provide the summary:"""

        return prompt

    def _parse_llm_response(self, llm_response: str, original_text: str) -> Dict[str, any]:
        """
        Parse structured data from LLM summary response

        Args:
            llm_response: Raw LLM output
            original_text: Original conversation for fallback

        Returns:
            Structured summary dictionary
        """
        lines = llm_response.strip().split('\n')

        summary = ""
        topics = []
        mood = "neutral"
        key_moments = []
        safety_concerns = []

        current_section = None

        for line in lines:
            line = line.strip()

            if line.startswith("SUMMARY:"):
                current_section = "summary"
                summary = line.replace("SUMMARY:", "").strip()
            elif line.startswith("TOPICS:"):
                current_section = "topics"
                topics_str = line.replace("TOPICS:", "").strip()
                topics = [t.strip() for t in topics_str.split(',') if t.strip()]
            elif line.startswith("MOOD:"):
                current_section = "mood"
                mood = line.replace("MOOD:", "").strip().lower()
            elif line.startswith("KEY_MOMENTS:"):
                current_section = "key_moments"
                moments_str = line.replace("KEY_MOMENTS:", "").strip()
                if moments_str:
                    key_moments.append(moments_str)
            elif line.startswith("SAFETY_CONCERNS:"):
                current_section = "safety_concerns"
                concerns_str = line.replace("SAFETY_CONCERNS:", "").strip()
                if concerns_str and concerns_str.lower() != "none":
                    safety_concerns.append(concerns_str)
            elif line and current_section:
                # Continue multi-line sections
                if current_section == "summary":
                    summary += " " + line
                elif current_section == "key_moments" and line:
                    key_moments.append(line)
                elif current_section == "safety_concerns" and line.lower() != "none":
                    safety_concerns.append(line)

        # Fallback values if parsing failed
        if not summary:
            summary = self._extract_simple_summary(original_text)
        if not topics:
            topics = ["chess", "learning"]
        if mood not in ["positive", "neutral", "frustrated", "confused", "engaged", "discouraged"]:
            mood = "neutral"

        return {
            "summary": summary,
            "topics": topics,
            "mood": mood,
            "key_moments": key_moments,
            "safety_concerns": safety_concerns
        }

    def _fallback_summary(self, conversation_text: str) -> Dict[str, any]:
        """
        Generate basic summary without LLM (fallback)

        Args:
            conversation_text: Conversation text

        Returns:
            Basic summary dictionary
        """
        # Count messages
        message_count = conversation_text.count("Child:") + conversation_text.count("Assistant:")

        # Extract first user message for context
        lines = conversation_text.split('\n')
        first_topic = "general discussion"

        for line in lines:
            if line.startswith("Child:"):
                first_topic = line.replace("Child:", "").strip()[:50]
                break

        return {
            "summary": f"Conversation with {message_count} messages. Started with: {first_topic}...",
            "topics": ["chess"],
            "mood": "neutral",
            "key_moments": [],
            "safety_concerns": []
        }

    def _extract_simple_summary(self, conversation_text: str) -> str:
        """
        Extract a simple summary from conversation text

        Args:
            conversation_text: The conversation

        Returns:
            Simple summary string
        """
        lines = conversation_text.split('\n')
        message_count = sum(1 for line in lines if line.startswith(("Child:", "Assistant:")))

        # Get first and last user messages
        user_messages = [line for line in lines if line.startswith("Child:")]

        if user_messages:
            first_msg = user_messages[0].replace("Child:", "").strip()[:60]
            return f"Conversation with {message_count} messages about {first_msg}..."

        return f"Conversation with {message_count} messages about chess."


# Global service instance
conversation_summary_service = ConversationSummaryService()
