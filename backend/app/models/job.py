"""Job model."""

from sqlalchemy import Column, String, Text, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Job(BaseModel):
    """Job posting model."""

    __tablename__ = "jobs"

    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    requirements = Column(Text, nullable=True)
    company = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)

    # Extracted features (stored as JSON)
    required_skills = Column(JSON, nullable=True)
    preferred_skills = Column(JSON, nullable=True)
    education_level = Column(String(100), nullable=True)
    experience_years = Column(Integer, nullable=True)

    # Embeddings for semantic matching (stored as JSON array)
    description_embedding = Column(JSON, nullable=True)

    # Foreign key
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    owner = relationship("User", back_populates="jobs")
    resumes = relationship("Resume", back_populates="job", cascade="all, delete-orphan")
    rankings = relationship("Ranking", back_populates="job", cascade="all, delete-orphan")
