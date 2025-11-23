"""Audit logging service for compliance tracking."""

from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import Request
from loguru import logger

from app.models.audit_log import AuditLog
from app.models.user import User


class AuditService:
    """Service for audit logging and compliance tracking."""

    # Action types
    ACTION_CREATE = "create"
    ACTION_UPDATE = "update"
    ACTION_DELETE = "delete"
    ACTION_VIEW = "view"
    ACTION_EXPORT = "export"
    ACTION_LOGIN = "login"
    ACTION_LOGOUT = "logout"
    ACTION_UPLOAD = "upload"
    ACTION_RANK = "rank"
    ACTION_ANONYMIZE = "anonymize"
    ACTION_GENERATE_REPORT = "generate_report"

    # Resource types
    RESOURCE_JOB = "job"
    RESOURCE_RESUME = "resume"
    RESOURCE_RANKING = "ranking"
    RESOURCE_USER = "user"
    RESOURCE_SETTINGS = "settings"
    RESOURCE_EXPORT = "export"
    RESOURCE_REPORT = "report"

    # Status types
    STATUS_SUCCESS = "success"
    STATUS_FAILURE = "failure"
    STATUS_WARNING = "warning"

    def __init__(self, db: Session):
        """Initialize audit service.

        Args:
            db: Database session
        """
        self.db = db

    def log_action(
        self,
        action: str,
        resource_type: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        resource_id: Optional[int] = None,
        description: Optional[str] = None,
        changes: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
        request: Optional[Request] = None,
        status: str = STATUS_SUCCESS,
        error_message: Optional[str] = None
    ) -> AuditLog:
        """Log an audit entry.

        Args:
            action: Action performed (create, update, delete, etc.)
            resource_type: Type of resource affected
            user_id: ID of user who performed action
            username: Username of user who performed action
            resource_id: ID of affected resource
            description: Human-readable description
            changes: Before/after changes (for updates)
            metadata: Additional context
            request: FastAPI request object
            status: Action status (success/failure/warning)
            error_message: Error message if failed

        Returns:
            Created audit log entry
        """
        try:
            # Extract request information
            ip_address = None
            user_agent = None
            request_path = None
            request_method = None

            if request:
                ip_address = self._get_client_ip(request)
                user_agent = request.headers.get("user-agent")
                request_path = str(request.url.path) if hasattr(request.url, "path") else None
                request_method = request.method

            # Create audit log entry
            audit_log = AuditLog(
                user_id=user_id,
                username=username,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                description=description,
                changes=changes,
                metadata=metadata,
                ip_address=ip_address,
                user_agent=user_agent,
                request_path=request_path,
                request_method=request_method,
                status=status,
                error_message=error_message
            )

            self.db.add(audit_log)
            self.db.commit()
            self.db.refresh(audit_log)

            logger.debug(
                f"Audit log created: {action} on {resource_type} "
                f"by user {username or 'unknown'} (status: {status})"
            )

            return audit_log

        except Exception as e:
            logger.error(f"Failed to create audit log: {str(e)}")
            self.db.rollback()
            # Don't fail the main operation if audit logging fails
            return None

    def log_login(
        self,
        user_id: int,
        username: str,
        request: Optional[Request] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """Log user login attempt.

        Args:
            user_id: User ID
            username: Username
            request: Request object
            success: Whether login was successful
            error_message: Error message if failed
        """
        return self.log_action(
            action=self.ACTION_LOGIN,
            resource_type=self.RESOURCE_USER,
            user_id=user_id if success else None,
            username=username,
            description=f"User {username} logged {'in successfully' if success else 'in failed'}",
            request=request,
            status=self.STATUS_SUCCESS if success else self.STATUS_FAILURE,
            error_message=error_message
        )

    def log_logout(
        self,
        user_id: int,
        username: str,
        request: Optional[Request] = None
    ):
        """Log user logout.

        Args:
            user_id: User ID
            username: Username
            request: Request object
        """
        return self.log_action(
            action=self.ACTION_LOGOUT,
            resource_type=self.RESOURCE_USER,
            user_id=user_id,
            username=username,
            description=f"User {username} logged out",
            request=request
        )

    def log_job_action(
        self,
        action: str,
        job_id: int,
        user_id: int,
        username: str,
        description: Optional[str] = None,
        changes: Optional[Dict] = None,
        request: Optional[Request] = None
    ):
        """Log job-related action.

        Args:
            action: Action type (create, update, delete)
            job_id: Job ID
            user_id: User ID
            username: Username
            description: Action description
            changes: Changes made (for updates)
            request: Request object
        """
        return self.log_action(
            action=action,
            resource_type=self.RESOURCE_JOB,
            user_id=user_id,
            username=username,
            resource_id=job_id,
            description=description or f"Job {action}d",
            changes=changes,
            request=request
        )

    def log_resume_upload(
        self,
        resume_id: int,
        job_id: int,
        user_id: int,
        username: str,
        filename: str,
        request: Optional[Request] = None
    ):
        """Log resume upload.

        Args:
            resume_id: Resume ID
            job_id: Job ID
            user_id: User ID
            username: Username
            filename: Uploaded filename
            request: Request object
        """
        return self.log_action(
            action=self.ACTION_UPLOAD,
            resource_type=self.RESOURCE_RESUME,
            user_id=user_id,
            username=username,
            resource_id=resume_id,
            description=f"Resume uploaded: {filename}",
            metadata={"job_id": job_id, "filename": filename},
            request=request
        )

    def log_ranking_action(
        self,
        ranking_id: int,
        job_id: int,
        resume_id: int,
        user_id: int,
        username: str,
        score: float,
        request: Optional[Request] = None
    ):
        """Log ranking creation.

        Args:
            ranking_id: Ranking ID
            job_id: Job ID
            resume_id: Resume ID
            user_id: User ID
            username: Username
            score: Overall score
            request: Request object
        """
        return self.log_action(
            action=self.ACTION_RANK,
            resource_type=self.RESOURCE_RANKING,
            user_id=user_id,
            username=username,
            resource_id=ranking_id,
            description=f"Resume ranked with score {score:.2f}",
            metadata={
                "job_id": job_id,
                "resume_id": resume_id,
                "overall_score": score
            },
            request=request
        )

    def log_export(
        self,
        export_type: str,
        resource_id: int,
        user_id: int,
        username: str,
        format: str = "csv",
        request: Optional[Request] = None
    ):
        """Log data export.

        Args:
            export_type: Type of export (rankings, analytics, report)
            resource_id: Resource ID (usually job_id)
            user_id: User ID
            username: Username
            format: Export format (csv, pdf, etc.)
            request: Request object
        """
        return self.log_action(
            action=self.ACTION_EXPORT,
            resource_type=self.RESOURCE_EXPORT,
            user_id=user_id,
            username=username,
            resource_id=resource_id,
            description=f"Data exported as {format}",
            metadata={"export_type": export_type, "format": format},
            request=request
        )

    def log_anonymization(
        self,
        resume_id: int,
        user_id: int,
        username: str,
        anonymization_level: str,
        changes_count: int,
        request: Optional[Request] = None
    ):
        """Log resume anonymization.

        Args:
            resume_id: Resume ID
            user_id: User ID
            username: Username
            anonymization_level: Level of anonymization
            changes_count: Number of changes made
            request: Request object
        """
        return self.log_action(
            action=self.ACTION_ANONYMIZE,
            resource_type=self.RESOURCE_RESUME,
            user_id=user_id,
            username=username,
            resource_id=resume_id,
            description=f"Resume anonymized (level: {anonymization_level})",
            metadata={
                "anonymization_level": anonymization_level,
                "changes_count": changes_count
            },
            request=request
        )

    def get_audit_logs(
        self,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """Retrieve audit logs with filters.

        Args:
            user_id: Filter by user ID
            action: Filter by action type
            resource_type: Filter by resource type
            resource_id: Filter by resource ID
            start_date: Start date filter
            end_date: End date filter
            status: Filter by status
            limit: Maximum results
            offset: Results offset for pagination

        Returns:
            List of audit logs
        """
        query = self.db.query(AuditLog)

        # Apply filters
        filters = []

        if user_id:
            filters.append(AuditLog.user_id == user_id)

        if action:
            filters.append(AuditLog.action == action)

        if resource_type:
            filters.append(AuditLog.resource_type == resource_type)

        if resource_id:
            filters.append(AuditLog.resource_id == resource_id)

        if start_date:
            filters.append(AuditLog.created_at >= start_date)

        if end_date:
            filters.append(AuditLog.created_at <= end_date)

        if status:
            filters.append(AuditLog.status == status)

        if filters:
            query = query.filter(and_(*filters))

        # Order by most recent first
        query = query.order_by(AuditLog.created_at.desc())

        # Apply pagination
        query = query.limit(limit).offset(offset)

        return query.all()

    def get_user_activity_summary(
        self,
        user_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get activity summary for a user.

        Args:
            user_id: User ID
            days: Number of days to look back

        Returns:
            Activity summary
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        logs = self.get_audit_logs(
            user_id=user_id,
            start_date=start_date,
            limit=1000
        )

        # Count by action type
        action_counts = {}
        resource_counts = {}

        for log in logs:
            action_counts[log.action] = action_counts.get(log.action, 0) + 1
            resource_counts[log.resource_type] = resource_counts.get(log.resource_type, 0) + 1

        return {
            "user_id": user_id,
            "period_days": days,
            "total_actions": len(logs),
            "actions_by_type": action_counts,
            "resources_accessed": resource_counts,
            "last_activity": logs[0].created_at.isoformat() if logs else None
        }

    def get_system_activity_summary(
        self,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get system-wide activity summary.

        Args:
            days: Number of days to look back

        Returns:
            System activity summary
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        logs = self.db.query(AuditLog).filter(
            AuditLog.created_at >= start_date
        ).all()

        # Count by various dimensions
        action_counts = {}
        resource_counts = {}
        user_activity = {}
        status_counts = {"success": 0, "failure": 0, "warning": 0}

        for log in logs:
            action_counts[log.action] = action_counts.get(log.action, 0) + 1
            resource_counts[log.resource_type] = resource_counts.get(log.resource_type, 0) + 1

            if log.user_id:
                user_activity[log.user_id] = user_activity.get(log.user_id, 0) + 1

            status_counts[log.status] = status_counts.get(log.status, 0) + 1

        return {
            "period_days": days,
            "total_actions": len(logs),
            "actions_by_type": action_counts,
            "resources_by_type": resource_counts,
            "unique_users": len(user_activity),
            "most_active_users": sorted(
                user_activity.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10],
            "status_distribution": status_counts
        }

    def _get_client_ip(self, request: Request) -> Optional[str]:
        """Extract client IP address from request.

        Args:
            request: FastAPI request

        Returns:
            Client IP address
        """
        # Check for forwarded IP (behind proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        # Check real IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct client
        if request.client:
            return request.client.host

        return None
