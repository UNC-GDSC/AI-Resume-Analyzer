"""Audit log API endpoints."""

from typing import Optional, List, Dict
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from loguru import logger

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.audit_service import AuditService

router = APIRouter()


@router.get("/logs", response_model=Dict)
async def get_audit_logs(
    action: Optional[str] = Query(None, description="Filter by action type"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    resource_id: Optional[int] = Query(None, description="Filter by resource ID"),
    days: Optional[int] = Query(30, description="Number of days to look back"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get audit logs for the current user.

    Args:
        action: Filter by action type
        resource_type: Filter by resource type
        resource_id: Filter by resource ID
        days: Number of days to look back
        status: Filter by status (success, failure, warning)
        limit: Maximum results
        offset: Results offset
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of audit logs
    """
    try:
        audit_service = AuditService(db)

        # Calculate start date
        start_date = datetime.utcnow() - timedelta(days=days) if days else None

        # Get logs for current user only (for security)
        user_id = int(current_user["sub"])

        logs = audit_service.get_audit_logs(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            start_date=start_date,
            status=status,
            limit=limit,
            offset=offset
        )

        # Format response
        formatted_logs = [
            {
                "id": log.id,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "description": log.description,
                "changes": log.changes,
                "metadata": log.metadata,
                "ip_address": log.ip_address,
                "status": log.status,
                "created_at": log.created_at.isoformat() if log.created_at else None
            }
            for log in logs
        ]

        logger.info(f"Retrieved {len(formatted_logs)} audit logs for user {user_id}")

        return {
            "total": len(formatted_logs),
            "limit": limit,
            "offset": offset,
            "logs": formatted_logs
        }

    except Exception as e:
        logger.error(f"Error retrieving audit logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve audit logs: {str(e)}"
        )


@router.get("/activity-summary", response_model=Dict)
async def get_user_activity_summary(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get activity summary for current user.

    Args:
        days: Number of days to analyze
        current_user: Current authenticated user
        db: Database session

    Returns:
        Activity summary with statistics
    """
    try:
        audit_service = AuditService(db)
        user_id = int(current_user["sub"])

        summary = audit_service.get_user_activity_summary(
            user_id=user_id,
            days=days
        )

        logger.info(f"Generated activity summary for user {user_id}")

        return summary

    except Exception as e:
        logger.error(f"Error generating activity summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate activity summary: {str(e)}"
        )


@router.get("/system-activity", response_model=Dict)
async def get_system_activity_summary(
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get system-wide activity summary (admin only in production).

    Args:
        days: Number of days to analyze
        current_user: Current authenticated user
        db: Database session

    Returns:
        System activity summary
    """
    try:
        # TODO: Add admin role check in production
        # For now, anyone can view system activity

        audit_service = AuditService(db)

        summary = audit_service.get_system_activity_summary(days=days)

        logger.info("Generated system activity summary")

        return summary

    except Exception as e:
        logger.error(f"Error generating system activity summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate system activity summary: {str(e)}"
        )


@router.get("/recent", response_model=List[Dict])
async def get_recent_activity(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get recent activity for current user.

    Args:
        limit: Maximum number of recent activities
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of recent activities
    """
    try:
        audit_service = AuditService(db)
        user_id = int(current_user["sub"])

        logs = audit_service.get_audit_logs(
            user_id=user_id,
            limit=limit,
            offset=0
        )

        activities = [
            {
                "action": log.action,
                "resource_type": log.resource_type,
                "description": log.description,
                "status": log.status,
                "created_at": log.created_at.isoformat() if log.created_at else None
            }
            for log in logs
        ]

        return activities

    except Exception as e:
        logger.error(f"Error retrieving recent activity: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve recent activity: {str(e)}"
        )


@router.get("/stats", response_model=Dict)
async def get_audit_statistics(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get audit statistics for current user.

    Args:
        days: Number of days to analyze
        current_user: Current authenticated user
        db: Database session

    Returns:
        Audit statistics
    """
    try:
        audit_service = AuditService(db)
        user_id = int(current_user["sub"])

        start_date = datetime.utcnow() - timedelta(days=days)

        logs = audit_service.get_audit_logs(
            user_id=user_id,
            start_date=start_date,
            limit=10000  # High limit for stats
        )

        # Calculate statistics
        total_actions = len(logs)
        success_count = len([l for l in logs if l.status == "success"])
        failure_count = len([l for l in logs if l.status == "failure"])

        # Group by date
        daily_counts = {}
        for log in logs:
            date_key = log.created_at.date().isoformat() if log.created_at else "unknown"
            daily_counts[date_key] = daily_counts.get(date_key, 0) + 1

        return {
            "period_days": days,
            "total_actions": total_actions,
            "success_rate": round((success_count / total_actions * 100), 2) if total_actions > 0 else 0,
            "failure_count": failure_count,
            "daily_activity": daily_counts,
            "average_daily_actions": round(total_actions / days, 2) if days > 0 else 0
        }

    except Exception as e:
        logger.error(f"Error calculating audit statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate audit statistics: {str(e)}"
        )
