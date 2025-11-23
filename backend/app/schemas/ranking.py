"""Ranking schemas."""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class RankingResponse(BaseModel):
    """Ranking response schema."""

    id: int
    job_id: int
    resume_id: int
    overall_score: float
    semantic_similarity_score: float
    skill_match_score: float
    experience_score: float
    education_score: float
    matched_skills: Optional[List[str]] = []
    missing_skills: Optional[List[str]] = []
    summary: Optional[str] = None
    strengths: Optional[List[str]] = []
    weaknesses: Optional[List[str]] = []
    rank_position: Optional[int] = None

    # Resume info (joined data)
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    filename: str

    created_at: datetime

    class Config:
        from_attributes = True
