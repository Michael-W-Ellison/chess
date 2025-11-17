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


# Favorites Category CRUD Endpoints


class FavoriteCreate(BaseModel):
    """Request model for creating a favorite"""

    key: str
    value: str


class FavoriteUpdate(BaseModel):
    """Request model for updating a favorite"""

    key: Optional[str] = None
    value: Optional[str] = None


@router.get("/profile/favorites")
async def get_favorites(user_id: int = 1, db: Session = Depends(get_db)):
    """
    Get all favorites for a user

    Args:
        user_id: User ID
        db: Database session

    Returns:
        List of favorites
    """
    try:
        favorites = memory_manager.get_favorites(user_id, db)

        return {
            "favorites": [fav.to_dict() for fav in favorites],
            "count": len(favorites),
        }

    except Exception as e:
        logger.error(f"Error getting favorites: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile/favorites/{favorite_id}")
async def get_favorite(
    favorite_id: int, user_id: int = 1, db: Session = Depends(get_db)
):
    """
    Get a specific favorite by ID

    Args:
        favorite_id: Favorite ID
        user_id: User ID
        db: Database session

    Returns:
        Favorite object
    """
    try:
        favorite = memory_manager.get_favorite_by_id(favorite_id, user_id, db)

        if not favorite:
            raise HTTPException(status_code=404, detail="Favorite not found")

        return favorite.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting favorite: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/profile/favorites")
async def create_favorite(
    favorite: FavoriteCreate, user_id: int = 1, db: Session = Depends(get_db)
):
    """
    Create a new favorite

    Args:
        favorite: Favorite data (key and value)
        user_id: User ID
        db: Database session

    Returns:
        Created favorite object
    """
    try:
        new_favorite = memory_manager.add_favorite(
            user_id, favorite.key, favorite.value, db
        )

        return {
            "message": "Favorite created successfully",
            "favorite": new_favorite.to_dict(),
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating favorite: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/profile/favorites/{favorite_id}")
async def update_favorite(
    favorite_id: int,
    favorite: FavoriteUpdate,
    user_id: int = 1,
    db: Session = Depends(get_db),
):
    """
    Update an existing favorite

    Args:
        favorite_id: Favorite ID
        favorite: Favorite update data
        user_id: User ID
        db: Database session

    Returns:
        Updated favorite object
    """
    try:
        updated_favorite = memory_manager.update_favorite(
            favorite_id, user_id, favorite.key, favorite.value, db
        )

        if not updated_favorite:
            raise HTTPException(status_code=404, detail="Favorite not found")

        return {
            "message": "Favorite updated successfully",
            "favorite": updated_favorite.to_dict(),
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating favorite: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/profile/favorites/{favorite_id}")
async def delete_favorite(
    favorite_id: int, user_id: int = 1, db: Session = Depends(get_db)
):
    """
    Delete a favorite

    Args:
        favorite_id: Favorite ID
        user_id: User ID
        db: Database session

    Returns:
        Success message
    """
    try:
        deleted = memory_manager.delete_favorite(favorite_id, user_id, db)

        if not deleted:
            raise HTTPException(status_code=404, detail="Favorite not found")

        return {"message": "Favorite deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting favorite: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Dislikes Category CRUD Endpoints


class DislikeCreate(BaseModel):
    """Request model for creating a dislike"""

    key: str
    value: str


class DislikeUpdate(BaseModel):
    """Request model for updating a dislike"""

    key: Optional[str] = None
    value: Optional[str] = None


@router.get("/profile/dislikes")
async def get_dislikes(user_id: int = 1, db: Session = Depends(get_db)):
    """
    Get all dislikes for a user

    Args:
        user_id: User ID
        db: Database session

    Returns:
        List of dislikes
    """
    try:
        dislikes = memory_manager.get_dislikes(user_id, db)

        return {
            "dislikes": [dislike.to_dict() for dislike in dislikes],
            "count": len(dislikes),
        }

    except Exception as e:
        logger.error(f"Error getting dislikes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile/dislikes/{dislike_id}")
async def get_dislike(
    dislike_id: int, user_id: int = 1, db: Session = Depends(get_db)
):
    """
    Get a specific dislike by ID

    Args:
        dislike_id: Dislike ID
        user_id: User ID
        db: Database session

    Returns:
        Dislike object
    """
    try:
        dislike = memory_manager.get_dislike_by_id(dislike_id, user_id, db)

        if not dislike:
            raise HTTPException(status_code=404, detail="Dislike not found")

        return dislike.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dislike: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/profile/dislikes")
async def create_dislike(
    dislike: DislikeCreate, user_id: int = 1, db: Session = Depends(get_db)
):
    """
    Create a new dislike

    Args:
        dislike: Dislike data (key and value)
        user_id: User ID
        db: Database session

    Returns:
        Created dislike object
    """
    try:
        new_dislike = memory_manager.add_dislike(
            user_id, dislike.key, dislike.value, db
        )

        return {
            "message": "Dislike created successfully",
            "dislike": new_dislike.to_dict(),
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating dislike: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/profile/dislikes/{dislike_id}")
async def update_dislike(
    dislike_id: int,
    dislike: DislikeUpdate,
    user_id: int = 1,
    db: Session = Depends(get_db),
):
    """
    Update an existing dislike

    Args:
        dislike_id: Dislike ID
        dislike: Dislike update data
        user_id: User ID
        db: Database session

    Returns:
        Updated dislike object
    """
    try:
        updated_dislike = memory_manager.update_dislike(
            dislike_id, user_id, dislike.key, dislike.value, db
        )

        if not updated_dislike:
            raise HTTPException(status_code=404, detail="Dislike not found")

        return {
            "message": "Dislike updated successfully",
            "dislike": updated_dislike.to_dict(),
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating dislike: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/profile/dislikes/{dislike_id}")
async def delete_dislike(
    dislike_id: int, user_id: int = 1, db: Session = Depends(get_db)
):
    """
    Delete a dislike

    Args:
        dislike_id: Dislike ID
        user_id: User ID
        db: Database session

    Returns:
        Success message
    """
    try:
        deleted = memory_manager.delete_dislike(dislike_id, user_id, db)

        if not deleted:
            raise HTTPException(status_code=404, detail="Dislike not found")

        return {"message": "Dislike deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting dislike: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Important People Category CRUD Endpoints


class PersonCreate(BaseModel):
    """Request model for creating an important person"""

    key: str
    value: str


class PersonUpdate(BaseModel):
    """Request model for updating an important person"""

    key: Optional[str] = None
    value: Optional[str] = None


@router.get("/profile/people")
async def get_people(user_id: int = 1, db: Session = Depends(get_db)):
    """
    Get all important people for a user

    Args:
        user_id: User ID
        db: Database session

    Returns:
        List of important people
    """
    try:
        people = memory_manager.get_people(user_id, db)

        return {
            "people": [person.to_dict() for person in people],
            "count": len(people),
        }

    except Exception as e:
        logger.error(f"Error getting people: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile/people/{person_id}")
async def get_person(
    person_id: int, user_id: int = 1, db: Session = Depends(get_db)
):
    """
    Get a specific person by ID

    Args:
        person_id: Person ID
        user_id: User ID
        db: Database session

    Returns:
        Person object
    """
    try:
        person = memory_manager.get_person_by_id(person_id, user_id, db)

        if not person:
            raise HTTPException(status_code=404, detail="Person not found")

        return person.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting person: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/profile/people")
async def create_person(
    person: PersonCreate, user_id: int = 1, db: Session = Depends(get_db)
):
    """
    Create a new important person

    Args:
        person: Person data (key and value)
        user_id: User ID
        db: Database session

    Returns:
        Created person object
    """
    try:
        new_person = memory_manager.add_person(
            user_id, person.key, person.value, db
        )

        return {
            "message": "Person created successfully",
            "person": new_person.to_dict(),
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating person: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/profile/people/{person_id}")
async def update_person(
    person_id: int,
    person: PersonUpdate,
    user_id: int = 1,
    db: Session = Depends(get_db),
):
    """
    Update an existing important person

    Args:
        person_id: Person ID
        person: Person update data
        user_id: User ID
        db: Database session

    Returns:
        Updated person object
    """
    try:
        updated_person = memory_manager.update_person(
            person_id, user_id, person.key, person.value, db
        )

        if not updated_person:
            raise HTTPException(status_code=404, detail="Person not found")

        return {
            "message": "Person updated successfully",
            "person": updated_person.to_dict(),
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating person: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/profile/people/{person_id}")
async def delete_person(
    person_id: int, user_id: int = 1, db: Session = Depends(get_db)
):
    """
    Delete an important person

    Args:
        person_id: Person ID
        user_id: User ID
        db: Database session

    Returns:
        Success message
    """
    try:
        deleted = memory_manager.delete_person(person_id, user_id, db)

        if not deleted:
            raise HTTPException(status_code=404, detail="Person not found")

        return {"message": "Person deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting person: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Goals Category CRUD Endpoints


class GoalCreate(BaseModel):
    """Request model for creating a goal"""

    key: str
    value: str


class GoalUpdate(BaseModel):
    """Request model for updating a goal"""

    key: Optional[str] = None
    value: Optional[str] = None


@router.get("/profile/goals")
async def get_goals(user_id: int = 1, db: Session = Depends(get_db)):
    """
    Get all goals for a user

    Args:
        user_id: User ID
        db: Database session

    Returns:
        List of goals
    """
    try:
        goals = memory_manager.get_goals(user_id, db)

        return {
            "goals": [goal.to_dict() for goal in goals],
            "count": len(goals),
        }

    except Exception as e:
        logger.error(f"Error getting goals: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile/goals/{goal_id}")
async def get_goal(
    goal_id: int, user_id: int = 1, db: Session = Depends(get_db)
):
    """
    Get a specific goal by ID

    Args:
        goal_id: Goal ID
        user_id: User ID
        db: Database session

    Returns:
        Goal object
    """
    try:
        goal = memory_manager.get_goal_by_id(goal_id, user_id, db)

        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")

        return goal.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting goal: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/profile/goals")
async def create_goal(
    goal: GoalCreate, user_id: int = 1, db: Session = Depends(get_db)
):
    """
    Create a new goal

    Args:
        goal: Goal data (key and value)
        user_id: User ID
        db: Database session

    Returns:
        Created goal object
    """
    try:
        new_goal = memory_manager.add_goal(
            user_id, goal.key, goal.value, db
        )

        return {
            "message": "Goal created successfully",
            "goal": new_goal.to_dict(),
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating goal: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/profile/goals/{goal_id}")
async def update_goal(
    goal_id: int,
    goal: GoalUpdate,
    user_id: int = 1,
    db: Session = Depends(get_db),
):
    """
    Update an existing goal

    Args:
        goal_id: Goal ID
        goal: Goal update data
        user_id: User ID
        db: Database session

    Returns:
        Updated goal object
    """
    try:
        updated_goal = memory_manager.update_goal(
            goal_id, user_id, goal.key, goal.value, db
        )

        if not updated_goal:
            raise HTTPException(status_code=404, detail="Goal not found")

        return {
            "message": "Goal updated successfully",
            "goal": updated_goal.to_dict(),
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating goal: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/profile/goals/{goal_id}")
async def delete_goal(
    goal_id: int, user_id: int = 1, db: Session = Depends(get_db)
):
    """
    Delete a goal

    Args:
        goal_id: Goal ID
        user_id: User ID
        db: Database session

    Returns:
        Success message
    """
    try:
        deleted = memory_manager.delete_goal(goal_id, user_id, db)

        if not deleted:
            raise HTTPException(status_code=404, detail="Goal not found")

        return {"message": "Goal deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting goal: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Achievements Category CRUD Endpoints


class AchievementCreate(BaseModel):
    """Request model for creating an achievement"""

    key: str
    value: str


class AchievementUpdate(BaseModel):
    """Request model for updating an achievement"""

    key: Optional[str] = None
    value: Optional[str] = None


@router.get("/profile/achievements")
async def get_achievements(user_id: int = 1, db: Session = Depends(get_db)):
    """
    Get all achievements for a user

    Args:
        user_id: User ID
        db: Database session

    Returns:
        List of achievements
    """
    try:
        achievements = memory_manager.get_achievements(user_id, db)

        return {
            "achievements": [achievement.to_dict() for achievement in achievements],
            "count": len(achievements),
        }

    except Exception as e:
        logger.error(f"Error getting achievements: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile/achievements/{achievement_id}")
async def get_achievement(
    achievement_id: int, user_id: int = 1, db: Session = Depends(get_db)
):
    """
    Get a specific achievement by ID

    Args:
        achievement_id: Achievement ID
        user_id: User ID
        db: Database session

    Returns:
        Achievement object
    """
    try:
        achievement = memory_manager.get_achievement_by_id(achievement_id, user_id, db)

        if not achievement:
            raise HTTPException(status_code=404, detail="Achievement not found")

        return achievement.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting achievement: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/profile/achievements")
async def create_achievement(
    achievement: AchievementCreate, user_id: int = 1, db: Session = Depends(get_db)
):
    """
    Create a new achievement

    Args:
        achievement: Achievement data (key and value)
        user_id: User ID
        db: Database session

    Returns:
        Created achievement object
    """
    try:
        new_achievement = memory_manager.add_achievement(
            user_id, achievement.key, achievement.value, db
        )

        return {
            "message": "Achievement created successfully",
            "achievement": new_achievement.to_dict(),
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating achievement: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/profile/achievements/{achievement_id}")
async def update_achievement(
    achievement_id: int,
    achievement: AchievementUpdate,
    user_id: int = 1,
    db: Session = Depends(get_db),
):
    """
    Update an existing achievement

    Args:
        achievement_id: Achievement ID
        achievement: Achievement update data
        user_id: User ID
        db: Database session

    Returns:
        Updated achievement object
    """
    try:
        updated_achievement = memory_manager.update_achievement(
            achievement_id, user_id, achievement.key, achievement.value, db
        )

        if not updated_achievement:
            raise HTTPException(status_code=404, detail="Achievement not found")

        return {
            "message": "Achievement updated successfully",
            "achievement": updated_achievement.to_dict(),
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating achievement: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/profile/achievements/{achievement_id}")
async def delete_achievement(
    achievement_id: int, user_id: int = 1, db: Session = Depends(get_db)
):
    """
    Delete an achievement

    Args:
        achievement_id: Achievement ID
        user_id: User ID
        db: Database session

    Returns:
        Success message
    """
    try:
        deleted = memory_manager.delete_achievement(achievement_id, user_id, db)

        if not deleted:
            raise HTTPException(status_code=404, detail="Achievement not found")

        return {"message": "Achievement deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting achievement: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Memory Search Endpoint


@router.get("/profile/search")
async def search_memories(
    keywords: str,
    user_id: int = 1,
    category: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Search memories by keywords

    Args:
        keywords: Search keywords (space-separated)
        user_id: User ID
        category: Optional category filter (favorite, dislike, person, goal, achievement)
        limit: Maximum number of results (default 20, max 100)
        db: Database session

    Returns:
        List of matching memories ranked by relevance
    """
    try:
        # Validate limit
        if limit > 100:
            limit = 100
        if limit < 1:
            limit = 20

        # Perform search
        results = memory_manager.search_memories(
            user_id=user_id,
            keywords=keywords,
            db=db,
            category=category,
            limit=limit
        )

        return {
            "results": [memory.to_dict() for memory in results],
            "count": len(results),
            "keywords": keywords,
            "category": category
        }

    except Exception as e:
        logger.error(f"Error searching memories: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Memory Relevance Ranking Endpoints


@router.get("/profile/top-memories")
async def get_top_memories(
    user_id: int = 1,
    limit: int = 10,
    category: Optional[str] = None,
    strategy: str = "combined",
    db: Session = Depends(get_db)
):
    """
    Get top most relevant memories for a user

    Args:
        user_id: User ID
        limit: Maximum number of results (default 10, max 50)
        category: Optional category filter (favorite, dislike, person, goal, achievement)
        strategy: Ranking strategy - "recency", "frequency", "confidence", or "combined"
        db: Database session

    Returns:
        List of top memories ranked by relevance with scores
    """
    try:
        # Validate parameters
        if limit > 50:
            limit = 50
        if limit < 1:
            limit = 10

        valid_strategies = ["recency", "frequency", "confidence", "combined"]
        if strategy not in valid_strategies:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid strategy. Must be one of: {', '.join(valid_strategies)}"
            )

        # Get top memories
        memories = memory_manager.get_top_memories(
            user_id=user_id,
            db=db,
            limit=limit,
            category=category,
            strategy=strategy
        )

        # Include relevance scores in response
        results = []
        for memory in memories:
            score = memory_manager.calculate_memory_relevance(memory, strategy)
            results.append({
                "memory": memory.to_dict(),
                "relevance_score": round(score, 2)
            })

        return {
            "results": results,
            "count": len(results),
            "strategy": strategy,
            "category": category
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting top memories: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile/memory-importance")
async def get_memory_importance(
    user_id: int = 1,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get breakdown of memory importance metrics

    Args:
        user_id: User ID
        category: Optional category filter
        db: Database session

    Returns:
        Comprehensive breakdown of memory importance by different criteria
    """
    try:
        breakdown = memory_manager.get_memory_importance_breakdown(
            user_id=user_id,
            db=db,
            category=category
        )

        return breakdown

    except Exception as e:
        logger.error(f"Error getting memory importance breakdown: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
