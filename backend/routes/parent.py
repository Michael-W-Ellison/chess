"""
Parent Dashboard API Routes
Endpoints for parents to monitor child safety and view safety flags
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

from database.database import get_db
from models.user import User
from models.safety import SafetyFlag
from services.safety_flag_service import safety_flag_service
from services.parent_notification_service import parent_notification_service

logger = logging.getLogger("chatbot.routes.parent")

router = APIRouter()


# Response models
class SafetyFlagResponse(BaseModel):
    """Safety flag information"""
    id: int
    user_id: int
    message_id: Optional[int]
    flag_type: str
    severity: str
    content_snippet: Optional[str]
    action_taken: Optional[str]
    timestamp: str
    parent_notified: bool


class SafetyStatsResponse(BaseModel):
    """Safety statistics"""
    total_flags: int
    by_severity: Dict[str, int]
    by_type: Dict[str, int]
    parent_notified: int
    parent_unnotified: int
    last_24_hours: int


class UserSafetySummaryResponse(BaseModel):
    """User safety summary"""
    user_id: int
    user_name: str
    total_flags_all_time: int
    total_flags_last_7_days: int
    critical_flags_count: int
    last_flag_timestamp: Optional[str]
    most_common_flag_type: Optional[str]
    requires_attention: bool


class NotificationHistoryResponse(BaseModel):
    """Notification history item"""
    timestamp: str
    severity: str
    flag_type: str
    content_snippet: Optional[str]
    action_taken: Optional[str]


# Endpoints
@router.get("/dashboard/overview", response_model=UserSafetySummaryResponse)
async def get_parent_dashboard_overview(
    user_id: int = Query(..., description="Child's user ID"),
    db: Session = Depends(get_db)
):
    """
    Get parent dashboard overview for a child

    Returns summary of safety events and current status

    Args:
        user_id: Child's user ID
        db: Database session

    Returns:
        Dashboard overview with safety summary
    """
    try:
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get safety summary
        summary = safety_flag_service.get_user_safety_summary(db, user_id)

        # Determine if requires attention (has critical flags or recent unnotified flags)
        critical_flags = safety_flag_service.get_critical_flags(
            db, user_id=user_id, include_notified=False
        )
        recent_unnotified = safety_flag_service.get_unnotified_flags(
            db, user_id=user_id, min_severity="high"
        )
        requires_attention = len(critical_flags) > 0 or len(recent_unnotified) > 0

        return UserSafetySummaryResponse(
            user_id=user_id,
            user_name=user.name or "User",
            total_flags_all_time=summary["total_flags_all_time"],
            total_flags_last_7_days=summary["total_flags_last_7_days"],
            critical_flags_count=summary["critical_flags_count"],
            last_flag_timestamp=summary["last_flag_timestamp"],
            most_common_flag_type=summary["most_common_flag_type"],
            requires_attention=requires_attention
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting parent dashboard overview: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/safety-flags/all", response_model=List[SafetyFlagResponse])
async def get_all_safety_flags(
    user_id: int = Query(..., description="Child's user ID"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of flags to return"),
    offset: int = Query(0, ge=0, description="Number of flags to skip"),
    db: Session = Depends(get_db)
):
    """
    Get all safety flags for a child

    Args:
        user_id: Child's user ID
        limit: Maximum number of results
        offset: Number to skip for pagination
        db: Database session

    Returns:
        List of all safety flags
    """
    try:
        flags = safety_flag_service.get_by_user(db, user_id, limit=limit, offset=offset)

        return [
            SafetyFlagResponse(
                id=flag.id,
                user_id=flag.user_id,
                message_id=flag.message_id,
                flag_type=flag.flag_type,
                severity=flag.severity,
                content_snippet=flag.content_snippet,
                action_taken=flag.action_taken,
                timestamp=flag.timestamp.isoformat() if flag.timestamp else "",
                parent_notified=flag.parent_notified
            )
            for flag in flags
        ]

    except Exception as e:
        logger.error(f"Error getting all safety flags: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/safety-flags/critical", response_model=List[SafetyFlagResponse])
async def get_critical_safety_flags(
    user_id: int = Query(..., description="Child's user ID"),
    include_notified: bool = Query(False, description="Include flags already notified"),
    since_days: Optional[int] = Query(None, ge=1, le=365, description="Only show flags from last N days"),
    db: Session = Depends(get_db)
):
    """
    Get critical severity safety flags for a child

    Critical flags indicate serious safety concerns that require immediate attention

    Args:
        user_id: Child's user ID
        include_notified: Whether to include flags where parent was already notified
        since_days: Only show flags from last N days
        db: Database session

    Returns:
        List of critical safety flags
    """
    try:
        since_date = None
        if since_days:
            since_date = datetime.now() - timedelta(days=since_days)

        flags = safety_flag_service.get_critical_flags(
            db,
            user_id=user_id,
            since_date=since_date,
            include_notified=include_notified
        )

        return [
            SafetyFlagResponse(
                id=flag.id,
                user_id=flag.user_id,
                message_id=flag.message_id,
                flag_type=flag.flag_type,
                severity=flag.severity,
                content_snippet=flag.content_snippet,
                action_taken=flag.action_taken,
                timestamp=flag.timestamp.isoformat() if flag.timestamp else "",
                parent_notified=flag.parent_notified
            )
            for flag in flags
        ]

    except Exception as e:
        logger.error(f"Error getting critical safety flags: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/safety-flags/unnotified", response_model=List[SafetyFlagResponse])
async def get_unnotified_safety_flags(
    user_id: int = Query(..., description="Child's user ID"),
    min_severity: Optional[str] = Query(None, description="Minimum severity (low, medium, high, critical)"),
    db: Session = Depends(get_db)
):
    """
    Get safety flags that haven't been reviewed/notified

    Args:
        user_id: Child's user ID
        min_severity: Minimum severity level to include
        db: Database session

    Returns:
        List of unnotified safety flags
    """
    try:
        if min_severity and min_severity not in ["low", "medium", "high", "critical"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid severity. Must be one of: low, medium, high, critical"
            )

        flags = safety_flag_service.get_unnotified_flags(
            db,
            user_id=user_id,
            min_severity=min_severity
        )

        return [
            SafetyFlagResponse(
                id=flag.id,
                user_id=flag.user_id,
                message_id=flag.message_id,
                flag_type=flag.flag_type,
                severity=flag.severity,
                content_snippet=flag.content_snippet,
                action_taken=flag.action_taken,
                timestamp=flag.timestamp.isoformat() if flag.timestamp else "",
                parent_notified=flag.parent_notified
            )
            for flag in flags
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting unnotified safety flags: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/safety-flags/by-severity/{severity}", response_model=List[SafetyFlagResponse])
async def get_safety_flags_by_severity(
    severity: str,
    user_id: int = Query(..., description="Child's user ID"),
    since_days: Optional[int] = Query(None, ge=1, le=365, description="Only show flags from last N days"),
    db: Session = Depends(get_db)
):
    """
    Get safety flags filtered by severity level

    Args:
        severity: Severity level (low, medium, high, critical)
        user_id: Child's user ID
        since_days: Only show flags from last N days
        db: Database session

    Returns:
        List of safety flags matching severity
    """
    try:
        if severity not in ["low", "medium", "high", "critical"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid severity. Must be one of: low, medium, high, critical"
            )

        since_date = None
        if since_days:
            since_date = datetime.now() - timedelta(days=since_days)

        flags = safety_flag_service.get_by_severity(
            db,
            severity=severity,
            user_id=user_id,
            since_date=since_date
        )

        return [
            SafetyFlagResponse(
                id=flag.id,
                user_id=flag.user_id,
                message_id=flag.message_id,
                flag_type=flag.flag_type,
                severity=flag.severity,
                content_snippet=flag.content_snippet,
                action_taken=flag.action_taken,
                timestamp=flag.timestamp.isoformat() if flag.timestamp else "",
                parent_notified=flag.parent_notified
            )
            for flag in flags
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting safety flags by severity: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/safety-flags/by-type/{flag_type}", response_model=List[SafetyFlagResponse])
async def get_safety_flags_by_type(
    flag_type: str,
    user_id: int = Query(..., description="Child's user ID"),
    db: Session = Depends(get_db)
):
    """
    Get safety flags filtered by type

    Args:
        flag_type: Flag type (crisis, profanity, bullying, inappropriate_request, abuse)
        user_id: Child's user ID
        db: Database session

    Returns:
        List of safety flags matching type
    """
    try:
        valid_types = ["crisis", "profanity", "bullying", "inappropriate_request", "abuse"]
        if flag_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid flag type. Must be one of: {', '.join(valid_types)}"
            )

        flags = safety_flag_service.get_by_type(db, flag_type, user_id=user_id)

        return [
            SafetyFlagResponse(
                id=flag.id,
                user_id=flag.user_id,
                message_id=flag.message_id,
                flag_type=flag.flag_type,
                severity=flag.severity,
                content_snippet=flag.content_snippet,
                action_taken=flag.action_taken,
                timestamp=flag.timestamp.isoformat() if flag.timestamp else "",
                parent_notified=flag.parent_notified
            )
            for flag in flags
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting safety flags by type: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/safety-flags/recent", response_model=List[SafetyFlagResponse])
async def get_recent_safety_flags(
    user_id: int = Query(..., description="Child's user ID"),
    hours: int = Query(24, ge=1, le=168, description="Number of hours to look back"),
    db: Session = Depends(get_db)
):
    """
    Get recent safety flags from the last N hours

    Args:
        user_id: Child's user ID
        hours: Number of hours to look back (max 168 = 1 week)
        db: Database session

    Returns:
        List of recent safety flags
    """
    try:
        flags = safety_flag_service.get_recent_flags(db, user_id=user_id, hours=hours)

        return [
            SafetyFlagResponse(
                id=flag.id,
                user_id=flag.user_id,
                message_id=flag.message_id,
                flag_type=flag.flag_type,
                severity=flag.severity,
                content_snippet=flag.content_snippet,
                action_taken=flag.action_taken,
                timestamp=flag.timestamp.isoformat() if flag.timestamp else "",
                parent_notified=flag.parent_notified
            )
            for flag in flags
        ]

    except Exception as e:
        logger.error(f"Error getting recent safety flags: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/safety-flags/{flag_id}", response_model=SafetyFlagResponse)
async def get_safety_flag_detail(
    flag_id: int,
    user_id: int = Query(..., description="Child's user ID"),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific safety flag

    Args:
        flag_id: Safety flag ID
        user_id: Child's user ID (for authorization)
        db: Database session

    Returns:
        Safety flag details
    """
    try:
        flag = safety_flag_service.get_by_id(db, flag_id)

        if not flag:
            raise HTTPException(status_code=404, detail="Safety flag not found")

        # Verify the flag belongs to the specified user (authorization check)
        if flag.user_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to view this safety flag"
            )

        return SafetyFlagResponse(
            id=flag.id,
            user_id=flag.user_id,
            message_id=flag.message_id,
            flag_type=flag.flag_type,
            severity=flag.severity,
            content_snippet=flag.content_snippet,
            action_taken=flag.action_taken,
            timestamp=flag.timestamp.isoformat() if flag.timestamp else "",
            parent_notified=flag.parent_notified
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting safety flag detail: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics", response_model=SafetyStatsResponse)
async def get_safety_statistics(
    user_id: int = Query(..., description="Child's user ID"),
    since_days: Optional[int] = Query(None, ge=1, le=365, description="Statistics from last N days"),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive safety statistics for a child

    Args:
        user_id: Child's user ID
        since_days: Only include flags from last N days
        db: Database session

    Returns:
        Safety statistics breakdown
    """
    try:
        since_date = None
        if since_days:
            since_date = datetime.now() - timedelta(days=since_days)

        stats = safety_flag_service.get_stats(db, user_id=user_id, since_date=since_date)

        return SafetyStatsResponse(
            total_flags=stats["total_flags"],
            by_severity=stats["by_severity"],
            by_type=stats["by_type"],
            parent_notified=stats["parent_notified"],
            parent_unnotified=stats["parent_unnotified"],
            last_24_hours=stats["last_24_hours"]
        )

    except Exception as e:
        logger.error(f"Error getting safety statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notifications/history", response_model=List[NotificationHistoryResponse])
async def get_notification_history(
    user_id: int = Query(..., description="Child's user ID"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of notifications to return"),
    db: Session = Depends(get_db)
):
    """
    Get parent notification history for a child

    Args:
        user_id: Child's user ID
        limit: Maximum number of notifications
        db: Database session

    Returns:
        List of past parent notifications
    """
    try:
        history = parent_notification_service.get_notification_history(
            user_id=user_id,
            db=db,
            limit=limit
        )

        return [
            NotificationHistoryResponse(
                timestamp=notification["timestamp"],
                severity=notification["severity"],
                flag_type=notification["flag_type"],
                content_snippet=notification["content_snippet"],
                action_taken=notification["action_taken"]
            )
            for notification in history
        ]

    except Exception as e:
        logger.error(f"Error getting notification history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/safety-flags/{flag_id}/acknowledge")
async def acknowledge_safety_flag(
    flag_id: int,
    user_id: int = Query(..., description="Child's user ID"),
    db: Session = Depends(get_db)
):
    """
    Mark a safety flag as acknowledged/reviewed by parent

    Args:
        flag_id: Safety flag ID
        user_id: Child's user ID (for authorization)
        db: Database session

    Returns:
        Success message
    """
    try:
        flag = safety_flag_service.get_by_id(db, flag_id)

        if not flag:
            raise HTTPException(status_code=404, detail="Safety flag not found")

        # Verify the flag belongs to the specified user
        if flag.user_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to acknowledge this safety flag"
            )

        # Mark as parent notified
        success = safety_flag_service.mark_parent_notified(db, flag_id)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to mark flag as acknowledged")

        logger.info(f"Parent acknowledged safety flag {flag_id} for user {user_id}")

        return {
            "success": True,
            "message": "Safety flag marked as acknowledged",
            "flag_id": flag_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging safety flag: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/safety-flags/acknowledge-multiple")
async def acknowledge_multiple_flags(
    flag_ids: List[int],
    user_id: int = Query(..., description="Child's user ID"),
    db: Session = Depends(get_db)
):
    """
    Mark multiple safety flags as acknowledged/reviewed by parent

    Args:
        flag_ids: List of safety flag IDs to acknowledge
        user_id: Child's user ID (for authorization)
        db: Database session

    Returns:
        Success message with count
    """
    try:
        if not flag_ids:
            raise HTTPException(status_code=400, detail="No flag IDs provided")

        # Verify all flags belong to the specified user
        for flag_id in flag_ids:
            flag = safety_flag_service.get_by_id(db, flag_id)
            if not flag:
                raise HTTPException(
                    status_code=404,
                    detail=f"Safety flag {flag_id} not found"
                )
            if flag.user_id != user_id:
                raise HTTPException(
                    status_code=403,
                    detail=f"Not authorized to acknowledge flag {flag_id}"
                )

        # Mark all as parent notified
        count = safety_flag_service.mark_multiple_parent_notified(db, flag_ids)

        logger.info(f"Parent acknowledged {count} safety flags for user {user_id}")

        return {
            "success": True,
            "message": f"Marked {count} safety flags as acknowledged",
            "count": count,
            "flag_ids": flag_ids
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging multiple safety flags: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
