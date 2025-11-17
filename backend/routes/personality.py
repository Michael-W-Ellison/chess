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
from services.feature_unlock_manager import feature_unlock_manager
from services.feature_gates import check_feature_access, get_feature_gate_message
from services.personality_drift_calculator import personality_drift_calculator

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


# Feature unlock endpoints
@router.get("/features/summary")
async def get_feature_summary(user_id: int = 1, db: Session = Depends(get_db)):
    """
    Get comprehensive feature summary for a user

    Args:
        user_id: User ID
        db: Database session

    Returns:
        Feature summary with unlocked/locked features
    """
    try:
        personality = (
            db.query(BotPersonality).filter(BotPersonality.user_id == user_id).first()
        )

        if not personality:
            raise HTTPException(status_code=404, detail="Personality not found")

        summary = feature_unlock_manager.get_feature_summary(personality)

        return {
            "success": True,
            "summary": summary,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting feature summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/features/unlocked")
async def get_unlocked_features(user_id: int = 1, db: Session = Depends(get_db)):
    """
    Get all unlocked features for a user

    Args:
        user_id: User ID
        db: Database session

    Returns:
        List of unlocked features
    """
    try:
        personality = (
            db.query(BotPersonality).filter(BotPersonality.user_id == user_id).first()
        )

        if not personality:
            raise HTTPException(status_code=404, detail="Personality not found")

        features = feature_unlock_manager.get_unlocked_features(
            personality.friendship_level
        )

        return {
            "success": True,
            "features": features,
            "count": len(features),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting unlocked features: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/features/locked")
async def get_locked_features(user_id: int = 1, db: Session = Depends(get_db)):
    """
    Get all locked features for a user

    Args:
        user_id: User ID
        db: Database session

    Returns:
        List of locked features
    """
    try:
        personality = (
            db.query(BotPersonality).filter(BotPersonality.user_id == user_id).first()
        )

        if not personality:
            raise HTTPException(status_code=404, detail="Personality not found")

        features = feature_unlock_manager.get_locked_features(
            personality.friendship_level
        )

        return {
            "success": True,
            "features": features,
            "count": len(features),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting locked features: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/features/check/{feature_id}")
async def check_feature(feature_id: str, user_id: int = 1, db: Session = Depends(get_db)):
    """
    Check if a specific feature is unlocked

    Args:
        feature_id: Feature identifier
        user_id: User ID
        db: Database session

    Returns:
        Feature unlock status and information
    """
    try:
        personality = (
            db.query(BotPersonality).filter(BotPersonality.user_id == user_id).first()
        )

        if not personality:
            raise HTTPException(status_code=404, detail="Personality not found")

        unlocked = check_feature_access(personality, feature_id)
        feature_info = feature_unlock_manager.get_feature_info(feature_id)

        if not feature_info:
            raise HTTPException(status_code=404, detail="Feature not found")

        response = {
            "success": True,
            "feature_id": feature_id,
            "unlocked": unlocked,
            "feature_info": feature_info,
        }

        # Add lock message if locked
        if not unlocked:
            response["lock_message"] = get_feature_gate_message(feature_id, personality)

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking feature: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class FeatureCheckRequest(BaseModel):
    """Request model for checking multiple features"""
    feature_ids: List[str]


@router.post("/features/check-multiple")
async def check_multiple_features(
    request: FeatureCheckRequest,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """
    Check multiple features at once

    Args:
        request: List of feature IDs to check
        user_id: User ID
        db: Database session

    Returns:
        Dictionary of feature statuses
    """
    try:
        personality = (
            db.query(BotPersonality).filter(BotPersonality.user_id == user_id).first()
        )

        if not personality:
            raise HTTPException(status_code=404, detail="Personality not found")

        results = feature_unlock_manager.check_multiple_features(
            request.feature_ids,
            personality.friendship_level
        )

        return {
            "success": True,
            "results": results,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking multiple features: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/features/by-level/{level}")
async def get_features_by_level(level: int):
    """
    Get all features that unlock at a specific level

    Args:
        level: Friendship level (1-10)

    Returns:
        List of features unlocking at that level
    """
    try:
        if level < 1 or level > 10:
            raise HTTPException(status_code=400, detail="Level must be between 1 and 10")

        features = feature_unlock_manager.get_features_by_level(level)

        return {
            "success": True,
            "level": level,
            "features": features,
            "count": len(features),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting features by level: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/features/by-category/{category}")
async def get_features_by_category(category: str, user_id: Optional[int] = None, db: Session = Depends(get_db)):
    """
    Get all features in a specific category

    Args:
        category: Feature category
        user_id: Optional user ID to filter by unlocked status
        db: Database session

    Returns:
        List of features in category
    """
    try:
        friendship_level = None

        if user_id:
            personality = (
                db.query(BotPersonality).filter(BotPersonality.user_id == user_id).first()
            )
            if personality:
                friendship_level = personality.friendship_level

        features = feature_unlock_manager.get_features_by_category(
            category,
            friendship_level
        )

        return {
            "success": True,
            "category": category,
            "features": features,
            "count": len(features),
            "filtered_by_level": friendship_level is not None,
        }

    except Exception as e:
        logger.error(f"Error getting features by category: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/features/categories")
async def get_feature_categories():
    """
    Get all feature categories

    Returns:
        Dictionary of categories
    """
    try:
        categories = feature_unlock_manager.get_all_categories()

        return {
            "success": True,
            "categories": categories,
        }

    except Exception as e:
        logger.error(f"Error getting categories: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Personality Drift Endpoints
# ============================================================================


@router.get("/drift/history")
async def get_drift_history(
    user_id: int = 1,
    trait_name: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get personality drift history for a user

    Args:
        user_id: User ID (default 1)
        trait_name: Optional trait name to filter by (humor, energy, curiosity, formality)
        limit: Maximum number of drift events to return (default 50)
        db: Database session

    Returns:
        List of drift events
    """
    try:
        drifts = personality_drift_calculator.get_drift_history(
            user_id, db, trait_name, limit
        )

        return {
            "success": True,
            "user_id": user_id,
            "trait_name": trait_name,
            "drift_events": [drift.to_dict() for drift in drifts],
            "count": len(drifts),
        }

    except Exception as e:
        logger.error(f"Error getting drift history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/drift/summary")
async def get_drift_summary(user_id: int = 1, db: Session = Depends(get_db)):
    """
    Get comprehensive drift summary for a user

    Args:
        user_id: User ID (default 1)
        db: Database session

    Returns:
        Drift summary with statistics
    """
    try:
        summary = personality_drift_calculator.get_drift_summary(user_id, db)

        return {
            "success": True,
            "user_id": user_id,
            "summary": summary,
        }

    except Exception as e:
        logger.error(f"Error getting drift summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/drift/timeline/{trait_name}")
async def get_trait_timeline(
    trait_name: str,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """
    Get timeline of changes for a specific trait

    Args:
        trait_name: Trait name (humor, energy, curiosity, formality)
        user_id: User ID (default 1)
        db: Database session

    Returns:
        Timeline of trait changes
    """
    try:
        # Validate trait name
        valid_traits = ["humor", "energy", "curiosity", "formality"]
        if trait_name not in valid_traits:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid trait name. Must be one of: {', '.join(valid_traits)}"
            )

        timeline = personality_drift_calculator.get_trait_timeline(
            user_id, trait_name, db
        )

        # Get current personality for current value
        personality = db.query(BotPersonality).filter(
            BotPersonality.user_id == user_id
        ).first()

        if not personality:
            raise HTTPException(status_code=404, detail="Personality not found")

        current_value = getattr(personality, trait_name)

        return {
            "success": True,
            "user_id": user_id,
            "trait_name": trait_name,
            "current_value": current_value,
            "timeline": timeline,
            "total_changes": len(timeline),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trait timeline: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class ManualTraitAdjustmentRequest(BaseModel):
    """Request model for manual trait adjustment"""
    user_id: int = 1
    trait_name: str
    new_value: float


@router.post("/drift/manual-adjust")
async def manual_adjust_trait(
    request: ManualTraitAdjustmentRequest,
    db: Session = Depends(get_db)
):
    """
    Manually adjust a personality trait

    Args:
        request: Adjustment request with user_id, trait_name, new_value
        db: Database session

    Returns:
        Drift event created
    """
    try:
        # Get personality
        personality = db.query(BotPersonality).filter(
            BotPersonality.user_id == request.user_id
        ).first()

        if not personality:
            raise HTTPException(status_code=404, detail="Personality not found")

        # Apply adjustment
        drift_event = personality_drift_calculator.manual_trait_adjustment(
            personality, request.trait_name, request.new_value, db
        )

        return {
            "success": True,
            "message": f"Trait {request.trait_name} adjusted successfully",
            "drift_event": drift_event.to_dict(),
            "new_personality": personality.to_dict(),
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adjusting trait: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/drift/stats")
async def get_drift_stats(user_id: int = 1, db: Session = Depends(get_db)):
    """
    Get drift statistics for all traits

    Args:
        user_id: User ID (default 1)
        db: Database session

    Returns:
        Statistics for each trait
    """
    try:
        summary = personality_drift_calculator.get_drift_summary(user_id, db)

        # Get current personality
        personality = db.query(BotPersonality).filter(
            BotPersonality.user_id == user_id
        ).first()

        if not personality:
            raise HTTPException(status_code=404, detail="Personality not found")

        current_traits = {
            "humor": personality.humor,
            "energy": personality.energy,
            "curiosity": personality.curiosity,
            "formality": personality.formality,
        }

        return {
            "success": True,
            "user_id": user_id,
            "current_traits": current_traits,
            "drift_stats": summary.get("by_trait", {}),
            "total_drift_events": summary.get("total_drifts", 0),
            "drift_by_trigger": summary.get("by_trigger", {}),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting drift stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/drift/recent")
async def get_recent_drifts(
    user_id: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get recent personality drift events

    Args:
        user_id: User ID (default 1)
        limit: Number of recent events to return (default 10)
        db: Database session

    Returns:
        Recent drift events
    """
    try:
        drifts = personality_drift_calculator.get_drift_history(
            user_id, db, trait_name=None, limit=limit
        )

        return {
            "success": True,
            "user_id": user_id,
            "recent_drifts": [drift.to_dict() for drift in drifts],
            "count": len(drifts),
        }

    except Exception as e:
        logger.error(f"Error getting recent drifts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
