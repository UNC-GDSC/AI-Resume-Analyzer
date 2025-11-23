"""Advanced search and filtering endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from typing import List, Optional
from app.database import get_db
from app.models.resume import Resume
from app.models.ranking import Ranking
from app.models.job import Job
from app.core.security import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/search", tags=["Search"])


class SearchFilters(BaseModel):
    """Search filter model."""
    min_score: Optional[float] = None
    max_score: Optional[float] = None
    required_skills: Optional[List[str]] = None
    min_experience: Optional[float] = None
    education_level: Optional[str] = None
    search_query: Optional[str] = None


@router.get("/resumes/job/{job_id}")
def advanced_search_resumes(
    job_id: int,
    min_score: Optional[float] = Query(None, ge=0, le=100),
    max_score: Optional[float] = Query(None, ge=0, le=100),
    required_skills: Optional[str] = Query(None),
    min_experience: Optional[float] = Query(None, ge=0),
    education_level: Optional[str] = Query(None),
    search_query: Optional[str] = Query(None),
    sort_by: str = Query("score", regex="^(score|name|date|experience)$"),
    order: str = Query("desc", regex="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Advanced search and filter resumes.

    Args:
        job_id: Job ID
        min_score: Minimum overall score
        max_score: Maximum overall score
        required_skills: Comma-separated list of required skills
        min_experience: Minimum years of experience
        education_level: Required education level
        search_query: Full-text search query
        sort_by: Sort field (score, name, date, experience)
        order: Sort order (asc, desc)
        page: Page number
        per_page: Results per page
        current_user: Current authenticated user
        db: Database session

    Returns:
        Filtered and sorted resume rankings
    """
    user_id = int(current_user["sub"])

    # Verify job ownership
    job = db.query(Job).filter(Job.id == job_id, Job.owner_id == user_id).first()
    if not job:
        return {"results": [], "total": 0, "page": page, "per_page": per_page}

    # Build query
    query = db.query(Ranking).join(Resume).filter(Ranking.job_id == job_id)

    # Apply filters
    if min_score is not None:
        query = query.filter(Ranking.overall_score >= min_score)

    if max_score is not None:
        query = query.filter(Ranking.overall_score <= max_score)

    if required_skills:
        skills_list = [s.strip().lower() for s in required_skills.split(",")]
        for skill in skills_list:
            query = query.filter(
                func.lower(func.cast(Resume.skills, db.String)).like(f"%{skill}%")
            )

    if min_experience is not None:
        query = query.filter(Resume.total_experience_years >= min_experience)

    if education_level:
        query = query.join(Resume).filter(
            func.lower(func.cast(Resume.education, db.String)).like(f"%{education_level.lower()}%")
        )

    if search_query:
        search_pattern = f"%{search_query.lower()}%"
        query = query.filter(
            or_(
                func.lower(Resume.candidate_name).like(search_pattern),
                func.lower(Resume.email).like(search_pattern),
                func.lower(Resume.raw_text).like(search_pattern)
            )
        )

    # Get total count
    total = query.count()

    # Apply sorting
    if sort_by == "score":
        if order == "desc":
            query = query.order_by(Ranking.overall_score.desc())
        else:
            query = query.order_by(Ranking.overall_score.asc())
    elif sort_by == "name":
        if order == "desc":
            query = query.order_by(Resume.candidate_name.desc())
        else:
            query = query.order_by(Resume.candidate_name.asc())
    elif sort_by == "date":
        if order == "desc":
            query = query.order_by(Ranking.created_at.desc())
        else:
            query = query.order_by(Ranking.created_at.asc())
    elif sort_by == "experience":
        if order == "desc":
            query = query.order_by(Resume.total_experience_years.desc())
        else:
            query = query.order_by(Resume.total_experience_years.asc())

    # Apply pagination
    offset = (page - 1) * per_page
    rankings = query.offset(offset).limit(per_page).all()

    # Format results
    results = [
        {
            "id": ranking.id,
            "resume_id": ranking.resume_id,
            "overall_score": ranking.overall_score,
            "semantic_similarity_score": ranking.semantic_similarity_score,
            "skill_match_score": ranking.skill_match_score,
            "experience_score": ranking.experience_score,
            "education_score": ranking.education_score,
            "candidate_name": ranking.resume.candidate_name,
            "candidate_email": ranking.resume.email,
            "matched_skills": ranking.matched_skills,
            "missing_skills": ranking.missing_skills,
            "total_experience_years": ranking.resume.total_experience_years,
            "created_at": ranking.created_at
        }
        for ranking in rankings
    ]

    return {
        "results": results,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    }


@router.get("/jobs")
def search_jobs(
    query: Optional[str] = Query(None),
    skills: Optional[str] = Query(None),
    min_resumes: Optional[int] = Query(None, ge=0),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Search user's job postings.

    Args:
        query: Search query for title/description
        skills: Required skills filter
        min_resumes: Minimum number of resumes
        page: Page number
        per_page: Results per page
        current_user: Current authenticated user
        db: Database session

    Returns:
        Filtered job postings
    """
    user_id = int(current_user["sub"])

    # Build query
    job_query = db.query(Job).filter(Job.owner_id == user_id)

    if query:
        search_pattern = f"%{query.lower()}%"
        job_query = job_query.filter(
            or_(
                func.lower(Job.title).like(search_pattern),
                func.lower(Job.description).like(search_pattern),
                func.lower(Job.company).like(search_pattern)
            )
        )

    if skills:
        skills_list = [s.strip().lower() for s in skills.split(",")]
        for skill in skills_list:
            job_query = job_query.filter(
                func.lower(func.cast(Job.required_skills, db.String)).like(f"%{skill}%")
            )

    # Get total
    total = job_query.count()

    # Pagination
    offset = (page - 1) * per_page
    jobs = job_query.offset(offset).limit(per_page).all()

    # Format results with resume counts
    results = []
    for job in jobs:
        resume_count = db.query(Resume).filter(Resume.job_id == job.id).count()

        if min_resumes is not None and resume_count < min_resumes:
            continue

        results.append({
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "required_skills": job.required_skills,
            "resume_count": resume_count,
            "created_at": job.created_at
        })

    return {
        "results": results,
        "total": len(results),
        "page": page,
        "per_page": per_page
    }
