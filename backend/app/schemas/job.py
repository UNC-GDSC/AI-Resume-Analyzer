"""Job schemas."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class JobBase(BaseModel):
    """Base job schema."""

    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=10)
    requirements: Optional[str] = None
    company: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=255)


class JobCreate(JobBase):
    """Job creation schema."""

    pass


class JobUpdate(BaseModel):
    """Job update schema."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=10)
    requirements: Optional[str] = None
    company: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=255)


class JobResponse(JobBase):
    """Job response schema."""

    id: int
    owner_id: int
    required_skills: Optional[List[str]] = []
    preferred_skills: Optional[List[str]] = []
    education_level: Optional[str] = None
    experience_years: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    resume_count: int = 0

    class Config:
        from_attributes = True
