"""Resume model."""

from sqlalchemy import Column, String, Text, Integer, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Resume(BaseModel):
    """Resume model."""

    __tablename__ = "resumes"

    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(10), nullable=False)

    # Parsed content
    raw_text = Column(Text, nullable=False)
    parsed_data = Column(JSON, nullable=True)

    # Extracted information
    candidate_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)

    # Skills and experience
    skills = Column(JSON, nullable=True)  # List of extracted skills
    education = Column(JSON, nullable=True)  # Education history
    experience = Column(JSON, nullable=True)  # Work experience
    total_experience_years = Column(Float, nullable=True)

    # Embeddings for semantic matching
    resume_embedding = Column(JSON, nullable=True)

    # Foreign key
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)

    # Relationships
    job = relationship("Job", back_populates="resumes")
    ranking = relationship(
        "Ranking", back_populates="resume", uselist=False, cascade="all, delete-orphan"
    )
