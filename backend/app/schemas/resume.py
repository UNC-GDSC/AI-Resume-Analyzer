"""Resume schemas."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class ResumeUpload(BaseModel):
    """Resume upload schema."""

    job_id: int


class ResumeResponse(BaseModel):
    """Resume response schema."""

    id: int
    job_id: int
    filename: str
    file_type: str
    candidate_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: Optional[List[str]] = []
    education: Optional[List[Dict]] = []
    total_experience_years: Optional[float] = 0.0
    created_at: datetime

    class Config:
        from_attributes = True
