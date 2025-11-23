"""Audit log model for compliance and tracking."""

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base


class AuditLog(Base):
    """Audit log for tracking all system activities."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Who performed the action
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    username = Column(String(255), nullable=True)

    # What action was performed
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False, index=True)  # job, resume, ranking, user, etc.
    resource_id = Column(Integer, nullable=True, index=True)

    # Details about the action
    description = Column(Text, nullable=True)
    changes = Column(JSON, nullable=True)  # Before/after changes
    metadata = Column(JSON, nullable=True)  # Additional context

    # Request information
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(String(500), nullable=True)
    request_path = Column(String(500), nullable=True)
    request_method = Column(String(10), nullable=True)

    # Status
    status = Column(String(20), nullable=False, default="success")  # success, failure, warning
    error_message = Column(Text, nullable=True)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    def __repr__(self):
        return f"<AuditLog {self.id}: {self.action} on {self.resource_type} by {self.username}>"
