"""User model."""

from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class User(BaseModel):
    """User model for authentication."""

    __tablename__ = "users"

    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)

    # Relationships
    jobs = relationship("Job", back_populates="owner", cascade="all, delete-orphan")
