"""
Personality API Routes
Endpoints for bot personality information
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict
import logging

from database.database import get_db
from models.personality import BotPersonality
from services.personality_manager import personality_manager

logger = logging.getLogger("chatbot.routes.personality")

router = APIRouter()


# Response models
class PersonalityResponse(BaseModel):
    """Bot personality state"""

    name: str
    traits: Dict[str, float]
    friendship_level: int
    total_conversations: int
    mood: str
    quirks: List[str]
    interests: List[str]
    catchphrase: str | None
    stats: Dict[str, int]


# Endpoints
@router.get("/personality", response_model=PersonalityResponse)
async def get_personality(user_id: int = 1, db: Session = Depends(get_db)):
    """
    Get current bot personality state

    Args:
        user_id: User ID (default 1)
        db: Database session

    Returns:
        Current personality with traits, mood, friendship level
    """
    try:
        personality = (
            db.query(BotPersonality).filter(BotPersonality.user_id == user_id).first()
        )

        if not personality:
            # Initialize personality for new user
            personality = personality_manager.initialize_personality(user_id, db)
            logger.info(f"Created new personality for user {user_id}")

        # Calculate days since met
        from datetime import datetime

        days_since_met = (datetime.now() - personality.created_at).days

        # TODO: Calculate current streak from conversation history
        current_streak = 0

        return PersonalityResponse(
            name=personality.name,
            traits={
                "humor": personality.humor,
                "energy": personality.energy,
                "curiosity": personality.curiosity,
                "formality": personality.formality,
            },
            friendship_level=personality.friendship_level,
            total_conversations=personality.total_conversations,
            mood=personality.mood,
            quirks=personality.get_quirks(),
            interests=personality.get_interests(),
            catchphrase=personality.catchphrase,
            stats={
                "totalConversations": personality.total_conversations,
                "daysSinceMet": days_since_met,
                "currentStreak": current_streak,
            },
        )

    except Exception as e:
        logger.error(f"Error getting personality: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/personality/description")
async def get_personality_description(user_id: int = 1, db: Session = Depends(get_db)):
    """
    Get human-readable personality description

    Args:
        user_id: User ID
        db: Database session

    Returns:
        Personality trait descriptions
    """
    try:
        personality = (
            db.query(BotPersonality).filter(BotPersonality.user_id == user_id).first()
        )

        if not personality:
            raise HTTPException(status_code=404, detail="Personality not found")

        descriptions = personality_manager.get_personality_description(personality)

        return {
            "name": personality.name,
            "descriptions": descriptions,
            "mood": personality.mood,
            "friendship_level": personality.friendship_level,
            "level_label": _get_friendship_label(personality.friendship_level),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting personality description: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _get_friendship_label(level: int) -> str:
    """Get friendship level label"""
    if level <= 2:
        return "New Friends"
    elif level <= 4:
        return "Good Friends"
    elif level <= 6:
        return "Close Friends"
    elif level <= 8:
        return "Best Friends"
    else:
        return "Lifelong Friends"
