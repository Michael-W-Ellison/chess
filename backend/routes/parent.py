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
from models.conversation import Conversation
from services.safety_flag_service import safety_flag_service
from services.parent_notification_service import parent_notification_service
from services.parent_preferences_service import parent_preferences_service
from services.conversation_summary_service import conversation_summary_service
from services.weekly_report_service import weekly_report_service
from services.report_scheduler import report_scheduler

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


@router.get("/safety-flags/stats", response_model=SafetyStatsResponse)
async def get_safety_flags_statistics(
    user_id: int = Query(..., description="Child's user ID"),
    since_days: Optional[int] = Query(None, ge=1, le=365, description="Calculate stats from last N days"),
    db: Session = Depends(get_db)
):
    """
    Get safety flags statistics for a child

    Provides aggregate statistics including:
    - Total number of flags
    - Breakdown by severity
    - Breakdown by type
    - Count of flags where parent was notified vs not notified
    - Flags from last 24 hours

    Args:
        user_id: Child's user ID
        since_days: Optional - only calculate stats from last N days
        db: Database session

    Returns:
        Safety flags statistics
    """
    try:
        since_date = None
        if since_days:
            since_date = datetime.now() - timedelta(days=since_days)

        # Get all flags for the user (optionally filtered by date)
        all_flags = safety_flag_service.get_by_user(
            db,
            user_id,
            limit=1000,  # Large limit to get all
            since_date=since_date
        )

        # Calculate statistics
        total_flags = len(all_flags)

        # By severity
        by_severity = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0
        }

        # By type
        by_type = {}

        # Notification counts
        parent_notified = 0
        parent_unnotified = 0

        # Last 24 hours
        last_24_hours = 0
        cutoff_time = datetime.now() - timedelta(hours=24)

        for flag in all_flags:
            # Severity
            severity = flag.severity.lower()
            if severity in by_severity:
                by_severity[severity] += 1

            # Type
            flag_type = flag.flag_type
            by_type[flag_type] = by_type.get(flag_type, 0) + 1

            # Notification status
            if flag.parent_notified:
                parent_notified += 1
            else:
                parent_unnotified += 1

            # Last 24 hours
            if flag.timestamp and flag.timestamp >= cutoff_time:
                last_24_hours += 1

        return SafetyStatsResponse(
            total_flags=total_flags,
            by_severity=by_severity,
            by_type=by_type,
            parent_notified=parent_notified,
            parent_unnotified=parent_unnotified,
            last_24_hours=last_24_hours
        )

    except Exception as e:
        logger.error(f"Error getting safety flags statistics: {e}", exc_info=True)
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


# ============================================================================
# Parent Notification Preferences Endpoints
# ============================================================================


class PreferencesResponse(BaseModel):
    """Parent notification preferences"""
    id: int
    user_id: int
    email: Optional[str]
    email_notifications_enabled: bool
    instant_notification_min_severity: str
    severity_filters: Dict[str, bool]
    flag_type_filters: Dict[str, bool]
    summary_settings: Dict[str, Optional[int | str]]
    content_settings: Dict[str, bool | int]
    quiet_hours: Dict[str, bool | Optional[int]]
    created_at: str
    updated_at: str


class PreferencesUpdateRequest(BaseModel):
    """Request model for updating preferences"""
    email: Optional[str] = None
    email_notifications_enabled: Optional[bool] = None
    instant_notification_min_severity: Optional[str] = None
    notify_on_critical: Optional[bool] = None
    notify_on_high: Optional[bool] = None
    notify_on_medium: Optional[bool] = None
    notify_on_low: Optional[bool] = None
    notify_on_crisis: Optional[bool] = None
    notify_on_abuse: Optional[bool] = None
    notify_on_bullying: Optional[bool] = None
    notify_on_profanity: Optional[bool] = None
    notify_on_inappropriate: Optional[bool] = None
    summary_frequency: Optional[str] = None
    summary_day_of_week: Optional[int] = None
    summary_hour: Optional[int] = None
    include_content_snippets: Optional[bool] = None
    max_snippet_length: Optional[int] = None
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[int] = None
    quiet_hours_end: Optional[int] = None


@router.get("/preferences", response_model=PreferencesResponse)
async def get_notification_preferences(
    user_id: int = Query(..., description="Child's user ID"),
    db: Session = Depends(get_db)
):
    """
    Get parent notification preferences for a child

    Args:
        user_id: Child's user ID
        db: Database session

    Returns:
        Parent notification preferences
    """
    try:
        prefs = parent_preferences_service.get_preferences(db, user_id)

        return PreferencesResponse(
            id=prefs.id,
            user_id=prefs.user_id,
            email=prefs.email,
            email_notifications_enabled=prefs.email_notifications_enabled,
            instant_notification_min_severity=prefs.instant_notification_min_severity,
            severity_filters={
                "critical": prefs.notify_on_critical,
                "high": prefs.notify_on_high,
                "medium": prefs.notify_on_medium,
                "low": prefs.notify_on_low,
            },
            flag_type_filters={
                "crisis": prefs.notify_on_crisis,
                "abuse": prefs.notify_on_abuse,
                "bullying": prefs.notify_on_bullying,
                "profanity": prefs.notify_on_profanity,
                "inappropriate": prefs.notify_on_inappropriate,
            },
            summary_settings={
                "frequency": prefs.summary_frequency,
                "day_of_week": prefs.summary_day_of_week,
                "hour": prefs.summary_hour,
            },
            content_settings={
                "include_snippets": prefs.include_content_snippets,
                "max_snippet_length": prefs.max_snippet_length,
            },
            quiet_hours={
                "enabled": prefs.quiet_hours_enabled,
                "start": prefs.quiet_hours_start,
                "end": prefs.quiet_hours_end,
            },
            created_at=prefs.created_at.isoformat() if prefs.created_at else "",
            updated_at=prefs.updated_at.isoformat() if prefs.updated_at else "",
        )

    except Exception as e:
        logger.error(f"Error getting notification preferences: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/preferences", response_model=PreferencesResponse)
async def update_notification_preferences(
    request: PreferencesUpdateRequest,
    user_id: int = Query(..., description="Child's user ID"),
    db: Session = Depends(get_db)
):
    """
    Update parent notification preferences

    Args:
        request: Preference updates
        user_id: Child's user ID
        db: Database session

    Returns:
        Updated parent notification preferences
    """
    try:
        # Convert request to updates dict, excluding None values
        updates = {k: v for k, v in request.dict().items() if v is not None}

        prefs = parent_preferences_service.update_preferences(db, user_id, updates)

        return PreferencesResponse(
            id=prefs.id,
            user_id=prefs.user_id,
            email=prefs.email,
            email_notifications_enabled=prefs.email_notifications_enabled,
            instant_notification_min_severity=prefs.instant_notification_min_severity,
            severity_filters={
                "critical": prefs.notify_on_critical,
                "high": prefs.notify_on_high,
                "medium": prefs.notify_on_medium,
                "low": prefs.notify_on_low,
            },
            flag_type_filters={
                "crisis": prefs.notify_on_crisis,
                "abuse": prefs.notify_on_abuse,
                "bullying": prefs.notify_on_bullying,
                "profanity": prefs.notify_on_profanity,
                "inappropriate": prefs.notify_on_inappropriate,
            },
            summary_settings={
                "frequency": prefs.summary_frequency,
                "day_of_week": prefs.summary_day_of_week,
                "hour": prefs.summary_hour,
            },
            content_settings={
                "include_snippets": prefs.include_content_snippets,
                "max_snippet_length": prefs.max_snippet_length,
            },
            quiet_hours={
                "enabled": prefs.quiet_hours_enabled,
                "start": prefs.quiet_hours_start,
                "end": prefs.quiet_hours_end,
            },
            created_at=prefs.created_at.isoformat() if prefs.created_at else "",
            updated_at=prefs.updated_at.isoformat() if prefs.updated_at else "",
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating notification preferences: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preferences/enable-all")
async def enable_all_notification_preferences(
    user_id: int = Query(..., description="Child's user ID"),
    db: Session = Depends(get_db)
):
    """
    Enable all notification types and severities

    Args:
        user_id: Child's user ID
        db: Database session

    Returns:
        Success message
    """
    try:
        parent_preferences_service.enable_all_notifications(db, user_id)

        logger.info(f"Enabled all notifications for user {user_id}")

        return {
            "success": True,
            "message": "All notifications enabled",
            "user_id": user_id
        }

    except Exception as e:
        logger.error(f"Error enabling all notifications: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preferences/disable-all")
async def disable_all_notification_preferences(
    user_id: int = Query(..., description="Child's user ID"),
    db: Session = Depends(get_db)
):
    """
    Disable all email notifications

    Args:
        user_id: Child's user ID
        db: Database session

    Returns:
        Success message
    """
    try:
        parent_preferences_service.disable_all_notifications(db, user_id)

        logger.info(f"Disabled all notifications for user {user_id}")

        return {
            "success": True,
            "message": "All notifications disabled",
            "user_id": user_id
        }

    except Exception as e:
        logger.error(f"Error disabling all notifications: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preferences/reset")
async def reset_notification_preferences(
    user_id: int = Query(..., description="Child's user ID"),
    db: Session = Depends(get_db)
):
    """
    Reset notification preferences to defaults

    Args:
        user_id: Child's user ID
        db: Database session

    Returns:
        Success message
    """
    try:
        parent_preferences_service.reset_to_defaults(db, user_id)

        logger.info(f"Reset notification preferences to defaults for user {user_id}")

        return {
            "success": True,
            "message": "Preferences reset to defaults",
            "user_id": user_id
        }

    except Exception as e:
        logger.error(f"Error resetting preferences: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ===========================
# Conversation Summary Routes
# ===========================

class ConversationSummaryResponse(BaseModel):
    """Conversation summary data"""
    conversation_id: int
    summary: str
    topics: List[str]
    mood: str
    key_moments: List[str]
    safety_concerns: List[str]
    message_count: int
    duration_seconds: Optional[int]


class ConversationListResponse(BaseModel):
    """Conversation list item"""
    id: int
    timestamp: str
    message_count: Optional[int]
    duration_seconds: Optional[int]
    summary: Optional[str]
    topics: List[str]
    mood: Optional[str]


@router.get("/conversations", response_model=List[ConversationListResponse])
async def get_user_conversations(
    user_id: int = Query(..., description="Child's user ID"),
    limit: int = Query(50, description="Max conversations to return"),
    offset: int = Query(0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """
    Get list of conversations for a child

    Args:
        user_id: Child's user ID
        limit: Maximum number of conversations to return
        offset: Offset for pagination
        db: Database session

    Returns:
        List of conversations with summaries
    """
    try:
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get conversations
        conversations = db.query(Conversation).filter(
            Conversation.user_id == user_id
        ).order_by(
            Conversation.timestamp.desc()
        ).limit(limit).offset(offset).all()

        # Format response
        result = []
        for conv in conversations:
            result.append({
                "id": conv.id,
                "timestamp": conv.timestamp.isoformat() if conv.timestamp else None,
                "message_count": conv.message_count,
                "duration_seconds": conv.duration_seconds,
                "summary": conv.conversation_summary,
                "topics": conv.get_topics(),
                "mood": conv.mood_detected
            })

        logger.info(f"Retrieved {len(result)} conversations for user {user_id}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving conversations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}/summary", response_model=ConversationSummaryResponse)
async def get_conversation_summary(
    conversation_id: int,
    user_id: int = Query(..., description="Child's user ID for verification"),
    db: Session = Depends(get_db)
):
    """
    Get summary for a specific conversation

    If summary doesn't exist, returns basic conversation info.

    Args:
        conversation_id: Conversation ID
        user_id: Child's user ID (for verification)
        db: Database session

    Returns:
        Conversation summary data
    """
    try:
        # Get conversation
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        ).first()

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Return existing summary or basic info
        return {
            "conversation_id": conversation.id,
            "summary": conversation.conversation_summary or "No summary available yet",
            "topics": conversation.get_topics(),
            "mood": conversation.mood_detected or "neutral",
            "key_moments": [],
            "safety_concerns": [],
            "message_count": conversation.message_count or len(conversation.messages),
            "duration_seconds": conversation.duration_seconds
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving conversation summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversations/{conversation_id}/generate-summary", response_model=ConversationSummaryResponse)
async def generate_conversation_summary(
    conversation_id: int,
    user_id: int = Query(..., description="Child's user ID for verification"),
    regenerate: bool = Query(False, description="Force regenerate even if summary exists"),
    db: Session = Depends(get_db)
):
    """
    Generate or regenerate summary for a conversation using LLM

    Args:
        conversation_id: Conversation ID
        user_id: Child's user ID (for verification)
        regenerate: Force regeneration even if summary exists
        db: Database session

    Returns:
        Generated conversation summary
    """
    try:
        # Verify conversation belongs to user
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        ).first()

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Check if summary exists and regenerate is False
        if conversation.conversation_summary and not regenerate:
            logger.info(f"Summary already exists for conversation {conversation_id}, skipping generation")
            return {
                "conversation_id": conversation.id,
                "summary": conversation.conversation_summary,
                "topics": conversation.get_topics(),
                "mood": conversation.mood_detected or "neutral",
                "key_moments": [],
                "safety_concerns": [],
                "message_count": conversation.message_count or len(conversation.messages),
                "duration_seconds": conversation.duration_seconds
            }

        # Generate summary
        logger.info(f"Generating summary for conversation {conversation_id}")
        summary_data = conversation_summary_service.generate_summary(conversation_id, db)

        return {
            "conversation_id": conversation_id,
            **summary_data,
            "message_count": conversation.message_count or len(conversation.messages),
            "duration_seconds": conversation.duration_seconds
        }

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating conversation summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversations/generate-summaries-batch")
async def generate_summaries_batch(
    user_id: int = Query(..., description="Child's user ID"),
    conversation_ids: List[int] = Query(..., description="List of conversation IDs"),
    db: Session = Depends(get_db)
):
    """
    Generate summaries for multiple conversations

    Args:
        user_id: Child's user ID
        conversation_ids: List of conversation IDs to summarize
        db: Database session

    Returns:
        Results for each conversation
    """
    try:
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Verify conversations belong to user
        conversations = db.query(Conversation).filter(
            Conversation.id.in_(conversation_ids),
            Conversation.user_id == user_id
        ).all()

        found_ids = [c.id for c in conversations]
        missing_ids = set(conversation_ids) - set(found_ids)

        if missing_ids:
            logger.warning(f"Some conversations not found or don't belong to user: {missing_ids}")

        # Generate summaries
        results = conversation_summary_service.generate_batch_summaries(found_ids, db)

        logger.info(f"Generated {len(results)} summaries for user {user_id}")

        return {
            "success": True,
            "processed": len(results),
            "missing": list(missing_ids),
            "results": results
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating batch summaries: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-notification")
async def send_test_notification(
    user_id: int = Query(..., description="Child's user ID"),
    db: Session = Depends(get_db)
):
    """
    Send a test notification email to parent

    This endpoint sends a sample safety notification email to verify
    email configuration and notification settings are working correctly.

    Args:
        user_id: Child's user ID
        db: Database session

    Returns:
        Success message
    """
    try:
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get parent preferences
        preferences = parent_preferences_service.get_preferences(db, user_id)

        if not preferences:
            raise HTTPException(
                status_code=404,
                detail="Parent preferences not found. Please configure email settings first."
            )

        if not preferences.email:
            raise HTTPException(
                status_code=400,
                detail="No email address configured. Please add a parent email address."
            )

        if not preferences.email_notifications_enabled:
            raise HTTPException(
                status_code=400,
                detail="Email notifications are disabled. Please enable them to send test notifications."
            )

        # Send test notification
        try:
            parent_notification_service.send_test_notification(
                parent_email=preferences.email,
                child_name=user.name or f"User {user_id}"
            )
        except Exception as e:
            logger.error(f"Failed to send test notification: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send test notification: {str(e)}"
            )

        logger.info(f"Test notification sent to {preferences.email} for user {user_id}")

        return {
            "success": True,
            "message": f"Test notification sent to {preferences.email}",
            "email": preferences.email
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending test notification: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Weekly/Daily Report Endpoints
# ============================================================================


class ReportDataResponse(BaseModel):
    """Report data structure"""
    user_id: int
    user_name: str
    period: str
    start_date: str
    end_date: str
    safety: Dict
    conversations: Dict
    engagement: Dict


class ReportSendResponse(BaseModel):
    """Report send result"""
    success: bool
    sent: bool
    to_email: Optional[str] = None
    period: str
    reason: Optional[str] = None
    error: Optional[str] = None


@router.get("/reports/preview", response_model=ReportDataResponse)
async def preview_report(
    user_id: int = Query(..., description="Child's user ID"),
    period: str = Query("weekly", description="Report period (daily or weekly)"),
    db: Session = Depends(get_db)
):
    """
    Preview report data without sending email

    Generates all report data including safety statistics, conversation summaries,
    and engagement metrics for the specified period.

    Args:
        user_id: Child's user ID
        period: Report period - "daily" (last 24 hours) or "weekly" (last 7 days)
        db: Database session

    Returns:
        Report data for preview
    """
    try:
        if period not in ["daily", "weekly"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid period. Must be 'daily' or 'weekly'"
            )

        # Generate report data
        report_data = weekly_report_service.generate_report_data(db, user_id, period)

        logger.info(f"Generated {period} report preview for user {user_id}")

        return ReportDataResponse(**report_data)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating report preview: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reports/send", response_model=ReportSendResponse)
async def send_report(
    user_id: int = Query(..., description="Child's user ID"),
    period: str = Query("weekly", description="Report period (daily or weekly)"),
    force_send: bool = Query(False, description="Send regardless of preferences"),
    db: Session = Depends(get_db)
):
    """
    Generate and send report via email

    Generates a comprehensive safety and activity report and sends it to the
    parent's configured email address. Respects notification preferences unless
    force_send is True.

    Args:
        user_id: Child's user ID
        period: Report period - "daily" (last 24 hours) or "weekly" (last 7 days)
        force_send: If True, send regardless of notification preferences
        db: Database session

    Returns:
        Send result with status
    """
    try:
        if period not in ["daily", "weekly"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid period. Must be 'daily' or 'weekly'"
            )

        # Generate and send report
        result = weekly_report_service.generate_and_send_report(
            db, user_id, period, force_send
        )

        if result.get("success"):
            logger.info(f"Successfully sent {period} report to {result.get('to_email')} for user {user_id}")
            return ReportSendResponse(
                success=True,
                sent=True,
                to_email=result.get("to_email"),
                period=period
            )
        else:
            # Report not sent due to preferences or configuration
            logger.info(f"Report not sent for user {user_id}: {result.get('reason', result.get('error'))}")
            return ReportSendResponse(
                success=False,
                sent=False,
                period=period,
                reason=result.get("reason"),
                error=result.get("error")
            )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/generate")
async def generate_report(
    user_id: int = Query(..., description="Child's user ID"),
    period: str = Query("weekly", description="Report period (daily or weekly)"),
    send_email: bool = Query(False, description="Send report via email"),
    db: Session = Depends(get_db)
):
    """
    Generate report and optionally send via email

    This is a convenience endpoint that can either:
    - Generate report data only (send_email=False) for preview
    - Generate and send report via email (send_email=True)

    Args:
        user_id: Child's user ID
        period: Report period - "daily" (last 24 hours) or "weekly" (last 7 days)
        send_email: If True, also send report via email
        db: Database session

    Returns:
        Report data and send status (if email was requested)
    """
    try:
        if period not in ["daily", "weekly"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid period. Must be 'daily' or 'weekly'"
            )

        # Generate report data
        report_data = weekly_report_service.generate_report_data(db, user_id, period)

        response = {
            "report_data": report_data,
            "email_sent": False
        }

        # Optionally send email
        if send_email:
            send_result = weekly_report_service.generate_and_send_report(
                db, user_id, period, force_send=False
            )
            response["email_sent"] = send_result.get("sent", False)
            response["send_result"] = {
                "success": send_result.get("success"),
                "to_email": send_result.get("to_email"),
                "reason": send_result.get("reason"),
                "error": send_result.get("error")
            }

        logger.info(f"Generated {period} report for user {user_id} (email_sent={response['email_sent']})")

        return response

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reports/trigger-scheduled-check")
async def trigger_scheduled_check():
    """
    Manually trigger the scheduled report check

    This endpoint is useful for testing the automated report scheduler.
    It will immediately check all users and send reports to those who are
    due based on their preferences.

    This bypasses the hourly schedule and runs the check immediately.

    Returns:
        Success message
    """
    try:
        logger.info("Manually triggering scheduled report check")
        report_scheduler.force_check_now()

        return {
            "success": True,
            "message": "Scheduled report check triggered. Check logs for results."
        }

    except Exception as e:
        logger.error(f"Error triggering scheduled check: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
