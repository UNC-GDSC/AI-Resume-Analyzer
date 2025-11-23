"""Ranking model."""

from sqlalchemy import Column, Integer, Float, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Ranking(BaseModel):
    """Resume ranking model."""

    __tablename__ = "rankings"

    # Foreign keys
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False, unique=True)

    # Overall score (0-100)
    overall_score = Column(Float, nullable=False, index=True)

    # Component scores (0-100 each)
    semantic_similarity_score = Column(Float, nullable=False)
    skill_match_score = Column(Float, nullable=False)
    experience_score = Column(Float, nullable=False)
    education_score = Column(Float, nullable=False)

    # Detailed breakdown
    matched_skills = Column(JSON, nullable=True)  # List of matched skills
    missing_skills = Column(JSON, nullable=True)  # List of missing required skills
    extra_skills = Column(JSON, nullable=True)  # List of additional relevant skills

    # Analysis summary
    summary = Column(Text, nullable=True)
    strengths = Column(JSON, nullable=True)  # List of candidate strengths
    weaknesses = Column(JSON, nullable=True)  # List of areas for improvement

    # Rank position (1-based)
    rank_position = Column(Integer, nullable=True, index=True)

    # Relationships
    job = relationship("Job", back_populates="rankings")
    resume = relationship("Resume", back_populates="ranking")
