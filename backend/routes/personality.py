"""
Personality API Routes
Endpoints for bot personality information
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging

from database.database import get_db
from models.personality import BotPersonality
from services.personality_manager import personality_manager
from services.friendship_progression import friendship_manager
from services.level_up_event_handler import level_up_event_handler

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


# Level-up event endpoints
@router.get("/friendship/level-up-events")
async def get_level_up_events(
    user_id: int = 1,
    limit: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get level-up event history for a user

    Args:
        user_id: User ID
        limit: Optional limit on number of events
        db: Database session

    Returns:
        List of level-up events
    """
    try:
        events = level_up_event_handler.get_event_history(user_id, db, limit)

        return {
            "success": True,
            "events": [event.to_dict() for event in events],
            "count": len(events),
        }

    except Exception as e:
        logger.error(f"Error getting level-up events: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/friendship/unacknowledged-events")
async def get_unacknowledged_events(user_id: int = 1, db: Session = Depends(get_db)):
    """
    Get unacknowledged level-up events for a user

    Args:
        user_id: User ID
        db: Database session

    Returns:
        List of unacknowledged level-up events
    """
    try:
        events = level_up_event_handler.get_unacknowledged_events(user_id, db)

        return {
            "success": True,
            "events": [event.to_dict() for event in events],
            "count": len(events),
        }

    except Exception as e:
        logger.error(f"Error getting unacknowledged events: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/friendship/should-celebrate")
async def should_celebrate(user_id: int = 1, db: Session = Depends(get_db)):
    """
    Check if there's a celebration to show the user

    Args:
        user_id: User ID
        db: Database session

    Returns:
        Whether to show celebration and event to celebrate
    """
    try:
        should_show, event = level_up_event_handler.should_show_celebration(user_id, db)

        return {
            "success": True,
            "should_celebrate": should_show,
            "event": event.to_dict() if event else None,
        }

    except Exception as e:
        logger.error(f"Error checking celebration: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/friendship/acknowledge-event/{event_id}")
async def acknowledge_level_up_event(event_id: int, db: Session = Depends(get_db)):
    """
    Mark a level-up event as acknowledged

    Args:
        event_id: Event ID
        db: Database session

    Returns:
        Updated event
    """
    try:
        event = level_up_event_handler.acknowledge_event(event_id, db)

        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

        return {
            "success": True,
            "event": event.to_dict(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging event: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/friendship/acknowledge-all-events")
async def acknowledge_all_level_up_events(user_id: int = 1, db: Session = Depends(get_db)):
    """
    Acknowledge all unacknowledged level-up events

    Args:
        user_id: User ID
        db: Database session

    Returns:
        Number of events acknowledged
    """
    try:
        count = level_up_event_handler.acknowledge_all_events(user_id, db)

        return {
            "success": True,
            "acknowledged_count": count,
        }

    except Exception as e:
        logger.error(f"Error acknowledging all events: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/friendship/event-summary")
async def get_event_summary(user_id: int = 1, db: Session = Depends(get_db)):
    """
    Get summary of level-up events for a user

    Args:
        user_id: User ID
        db: Database session

    Returns:
        Event summary with stats
    """
    try:
        summary = level_up_event_handler.get_event_summary(user_id, db)

        return {
            "success": True,
            "summary": summary,
        }

    except Exception as e:
        logger.error(f"Error getting event summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/friendship/level-rewards")
async def get_level_rewards():
    """
    Get all level rewards

    Returns:
        Dictionary mapping level to rewards
    """
    try:
        rewards = level_up_event_handler.get_all_level_rewards()

        return {
            "success": True,
            "rewards": rewards,
        }

    except Exception as e:
        logger.error(f"Error getting level rewards: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/friendship/level-rewards/{level}")
async def get_specific_level_rewards(level: int):
    """
    Get rewards for a specific level

    Args:
        level: Friendship level (1-10)

    Returns:
        List of rewards for that level
    """
    try:
        if level < 1 or level > 10:
            raise HTTPException(status_code=400, detail="Level must be between 1 and 10")

        rewards = level_up_event_handler.get_level_rewards(level)

        return {
            "success": True,
            "level": level,
            "rewards": rewards,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting level rewards: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
