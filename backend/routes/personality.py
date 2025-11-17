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
from services.friendship_progression import friendship_manager

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


# Friendship progression endpoints
@router.get("/friendship/progress")
async def get_friendship_progress(user_id: int = 1, db: Session = Depends(get_db)):
    """
    Get detailed friendship progression information

    Args:
        user_id: User ID
        db: Database session

    Returns:
        Friendship progress details including current level, points, and progress to next level
    """
    try:
        personality = (
            db.query(BotPersonality).filter(BotPersonality.user_id == user_id).first()
        )

        if not personality:
            raise HTTPException(status_code=404, detail="Personality not found")

        progress = friendship_manager.get_friendship_progress(personality)

        return {
            "success": True,
            "progress": progress,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting friendship progress: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/friendship/levels")
async def get_all_friendship_levels():
    """
    Get information about all friendship levels

    Returns:
        List of all friendship levels with details
    """
    try:
        return {
            "success": True,
            "levels": friendship_manager.friendship_levels,
        }

    except Exception as e:
        logger.error(f"Error getting friendship levels: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/friendship/level/{level}")
async def get_friendship_level_info(level: int):
    """
    Get information about a specific friendship level

    Args:
        level: Friendship level (1-10)

    Returns:
        Level information including name, description, perks
    """
    try:
        if level < 1 or level > 10:
            raise HTTPException(status_code=400, detail="Level must be between 1 and 10")

        level_info = friendship_manager.get_level_info(level)

        return {
            "success": True,
            "level_info": level_info,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting level info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class AddPointsRequest(BaseModel):
    """Request model for adding friendship points"""
    activity: str
    custom_points: int | None = None


@router.post("/friendship/add-points")
async def add_friendship_points_endpoint(
    request: AddPointsRequest,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """
    Add friendship points for an activity

    Args:
        request: Activity and optional custom points
        user_id: User ID
        db: Database session

    Returns:
        Updated personality and event information
    """
    try:
        personality = (
            db.query(BotPersonality).filter(BotPersonality.user_id == user_id).first()
        )

        if not personality:
            raise HTTPException(status_code=404, detail="Personality not found")

        personality, level_increased, event_info = friendship_manager.add_friendship_points(
            personality,
            request.activity,
            db,
            request.custom_points
        )

        return {
            "success": True,
            "personality": personality.to_dict(),
            "level_increased": level_increased,
            "event_info": event_info,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding friendship points: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/friendship/activities")
async def get_available_activities():
    """
    Get all available activities and their point values

    Returns:
        Dictionary of activity types and point rewards
    """
    try:
        activities = friendship_manager.get_available_activities()

        return {
            "success": True,
            "activities": activities,
        }

    except Exception as e:
        logger.error(f"Error getting activities: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/friendship/history")
async def get_friendship_history(user_id: int = 1, db: Session = Depends(get_db)):
    """
    Get friendship progression history summary

    Args:
        user_id: User ID
        db: Database session

    Returns:
        History summary with stats
    """
    try:
        personality = (
            db.query(BotPersonality).filter(BotPersonality.user_id == user_id).first()
        )

        if not personality:
            raise HTTPException(status_code=404, detail="Personality not found")

        history = friendship_manager.get_friendship_history_summary(personality, db)

        return {
            "success": True,
            "history": history,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting friendship history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/friendship/simulate/{target_level}")
async def simulate_level_progression(target_level: int):
    """
    Simulate how many points/activities needed for a target level

    Args:
        target_level: Target friendship level (1-10)

    Returns:
        Simulation results with estimates
    """
    try:
        if target_level < 1 or target_level > 10:
            raise HTTPException(status_code=400, detail="Level must be between 1 and 10")

        simulation = friendship_manager.simulate_points_needed_for_level(target_level)

        return {
            "success": True,
            "simulation": simulation,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error simulating progression: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
