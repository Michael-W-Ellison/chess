"""
Profile API Routes
Endpoints for user profile and memory information
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging

from database.database import get_db
from models.user import User
from models.memory import UserProfile
from services.memory_manager import memory_manager

logger = logging.getLogger("chatbot.routes.profile")

router = APIRouter()


# Response models
class ImportantPerson(BaseModel):
    """Important person information"""

    name: str
    relationship: str
    notes: Optional[str] = None


class Goal(BaseModel):
    """User goal"""

    description: str
    category: str
    dateSet: str
    achieved: bool = False


class ProfileResponse(BaseModel):
    """User profile information"""

    name: str
    age: Optional[int] = None
    grade: Optional[int] = None
    favorites: Dict[str, str]
    dislikes: Dict[str, str]
    importantPeople: List[dict]
    goals: List[str]
    achievements: List[str]


# Endpoints
@router.get("/profile", response_model=ProfileResponse)
async def get_profile(user_id: int = 1, db: Session = Depends(get_db)):
    """
    Get user profile data

    Args:
        user_id: User ID (default 1)
        db: Database session

    Returns:
        User profile with favorites, people, goals, achievements
    """
    try:
        # Get user
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            # Create default user
            user = User(id=user_id, name="User")
            db.add(user)
            db.commit()
            db.refresh(user)

        # Get profile summary
        profile_summary = memory_manager.get_user_profile_summary(user_id, db)

        return ProfileResponse(
            name=user.name or "User",
            age=user.age,
            grade=user.grade,
            favorites=profile_summary.get("favorites", {}),
            dislikes=profile_summary.get("dislikes", {}),
            importantPeople=profile_summary.get("important_people", []),
            goals=profile_summary.get("goals", []),
            achievements=profile_summary.get("achievements", []),
        )

    except Exception as e:
        logger.error(f"Error getting profile: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile/memories")
async def get_memories(
    user_id: int = 1, category: Optional[str] = None, db: Session = Depends(get_db)
):
    """
    Get user memories, optionally filtered by category

    Args:
        user_id: User ID
        category: Optional category filter
        db: Database session

    Returns:
        List of memory items
    """
    try:
        if category:
            memories = UserProfile.get_by_category(db, user_id, category)
        else:
            memories = db.query(UserProfile).filter(UserProfile.user_id == user_id).all()

        return {
            "memories": [memory.to_dict() for memory in memories],
            "count": len(memories),
        }

    except Exception as e:
        logger.error(f"Error getting memories: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/profile/update")
async def update_profile(
    name: Optional[str] = None,
    age: Optional[int] = None,
    grade: Optional[int] = None,
    user_id: int = 1,
    db: Session = Depends(get_db),
):
    """
    Update user profile information

    Args:
        name: User name
        age: User age
        grade: User grade
        user_id: User ID
        db: Database session

    Returns:
        Updated profile
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            user = User(id=user_id)
            db.add(user)

        if name:
            user.name = name
        if age is not None:
            user.age = age
        if grade is not None:
            user.grade = grade

        db.commit()
        db.refresh(user)

        logger.info(f"Updated profile for user {user_id}")

        return user.to_dict()

    except Exception as e:
        logger.error(f"Error updating profile: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
