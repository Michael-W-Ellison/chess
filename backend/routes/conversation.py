"""
Conversation API Routes
Endpoints for chat conversation management
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import logging

from database.database import get_db
from services.conversation_manager import conversation_manager

logger = logging.getLogger("chatbot.routes.conversation")

router = APIRouter()


# Request/Response models
class StartConversationResponse(BaseModel):
    """Response for starting a conversation"""

    conversation_id: int
    greeting: str
    personality: dict


class SendMessageRequest(BaseModel):
    """Request to send a message"""

    content: str
    conversation_id: int
    user_id: int = 1  # Default user ID (single-user desktop app)


class SendMessageResponse(BaseModel):
    """Response with bot's reply"""

    message_id: int
    content: str
    timestamp: str
    metadata: dict


class EndConversationRequest(BaseModel):
    """Request to end a conversation"""

    conversation_id: int
    user_id: int = 1


# Endpoints
@router.post("/conversation/start", response_model=StartConversationResponse)
async def start_conversation(user_id: int = 1, db: Session = Depends(get_db)):
    """
    Start a new conversation session

    Args:
        user_id: User ID (default 1 for single-user app)
        db: Database session

    Returns:
        Conversation info with greeting message
    """
    try:
        result = conversation_manager.start_conversation(user_id, db)

        logger.info(f"Started conversation {result['conversation_id']} for user {user_id}")

        return StartConversationResponse(
            conversation_id=result["conversation_id"],
            greeting=result["greeting"],
            personality=result["personality"],
        )

    except Exception as e:
        logger.error(f"Error starting conversation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/message", response_model=SendMessageResponse)
async def send_message(request: SendMessageRequest, db: Session = Depends(get_db)):
    """
    Send a message and get bot's response

    Args:
        request: Message request with content, conversation_id, user_id
        db: Database session

    Returns:
        Bot's response message
    """
    try:
        result = conversation_manager.process_message(
            user_message=request.content,
            conversation_id=request.conversation_id,
            user_id=request.user_id,
            db=db,
        )

        # Get the last message (bot's response) from database
        from models.conversation import Message
        from datetime import datetime

        last_message = (
            db.query(Message)
            .filter(
                Message.conversation_id == request.conversation_id, Message.role == "assistant"
            )
            .order_by(Message.timestamp.desc())
            .first()
        )

        if not last_message:
            raise HTTPException(status_code=500, detail="Failed to retrieve response")

        logger.info(
            f"Processed message in conversation {request.conversation_id}: "
            f"{len(result['content'])} chars"
        )

        return SendMessageResponse(
            message_id=last_message.id,
            content=result["content"],
            timestamp=last_message.timestamp.isoformat(),
            metadata=result.get("metadata", {}),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversation/end")
async def end_conversation(request: EndConversationRequest, db: Session = Depends(get_db)):
    """
    End a conversation session

    Args:
        request: End conversation request
        db: Database session

    Returns:
        Success confirmation
    """
    try:
        conversation_manager.end_conversation(request.conversation_id, db)

        logger.info(f"Ended conversation {request.conversation_id}")

        return {"success": True, "message": "Conversation ended successfully"}

    except Exception as e:
        logger.error(f"Error ending conversation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversation/{conversation_id}")
async def get_conversation(conversation_id: int, db: Session = Depends(get_db)):
    """
    Get conversation details

    Args:
        conversation_id: Conversation ID
        db: Database session

    Returns:
        Conversation details with messages
    """
    try:
        from models.conversation import Conversation

        conversation = (
            db.query(Conversation).filter(Conversation.id == conversation_id).first()
        )

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return conversation.to_dict(include_messages=True)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving conversation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
