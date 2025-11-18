"""
Tests for Conversation Summary Service
"""

import pytest
from unittest.mock import Mock
from datetime import datetime

from services.conversation_summary_service import ConversationSummaryService
from models.conversation import Message


class TestConversationSummaryService:
    """Test suite for ConversationSummaryService"""

    @pytest.fixture
    def service(self):
        return ConversationSummaryService()

    @pytest.fixture
    def sample_messages(self):
        return [
            Message(
                id=1,
                conversation_id=1,
                role="user",
                content="How do I castle in chess?",
                timestamp=datetime.now()
            ),
            Message(
                id=2,
                conversation_id=1,
                role="assistant",
                content="Castling is a special move involving your king and rook.",
                timestamp=datetime.now()
            ),
        ]

    def test_build_conversation_text(self, service, sample_messages):
        """Test building formatted conversation text"""
        text = service._build_conversation_text(sample_messages)

        assert "Child: How do I castle in chess?" in text
        assert "Assistant: Castling is a special move" in text
        assert "\n\n" in text

    def test_fallback_summary(self, service):
        """Test fallback summary when LLM unavailable"""
        conversation_text = "Child: How do I castle?"

        result = service._fallback_summary(conversation_text)

        assert result["summary"]
        assert result["topics"] == ["chess"]
        assert result["mood"] == "neutral"
        assert isinstance(result["key_moments"], list)
        assert isinstance(result["safety_concerns"], list)

    def test_extract_simple_summary(self, service):
        """Test simple summary extraction"""
        conversation_text = "Child: How do I improve at chess?\nAssistant: Practice tactics daily."

        summary = service._extract_simple_summary(conversation_text)

        assert "How do I improve at chess?" in summary
        assert "chess" in summary.lower()

    def test_parse_llm_response(self, service):
        """Test parsing structured LLM response"""
        llm_response = """SUMMARY: Child learned about castling and pawn structure.

TOPICS: castling, pawn structure, tactics

MOOD: engaged

KEY_MOMENTS: Understood why castling is important for king safety

SAFETY_CONCERNS: None"""

        result = service._parse_llm_response(llm_response, "test conversation")

        assert "castling" in result["summary"].lower()
        assert "castling" in result["topics"]
        assert result["mood"] == "engaged"
        assert len(result["key_moments"]) > 0
        assert len(result["safety_concerns"]) == 0

    def test_parse_llm_response_with_safety_concerns(self, service):
        """Test parsing LLM response with safety concerns"""
        llm_response = """SUMMARY: Child expressed frustration about losses.

TOPICS: losing, emotions

MOOD: frustrated

KEY_MOMENTS: Mentioned feeling upset after losing

SAFETY_CONCERNS: Child may be experiencing heightened negative emotions"""

        result = service._parse_llm_response(llm_response, "test")

        assert result["mood"] == "frustrated"
        assert len(result["safety_concerns"]) > 0

    def test_build_summary_prompt(self, service):
        """Test prompt building for LLM"""
        conversation = "Child: I'm sad\nAssistant: I'm here to help."

        prompt = service._build_summary_prompt(conversation)

        assert "SUMMARY:" in prompt
        assert "TOPICS:" in prompt
        assert "MOOD:" in prompt
        assert conversation in prompt
