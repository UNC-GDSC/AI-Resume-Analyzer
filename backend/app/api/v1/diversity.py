"""Diversity and inclusion analytics endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.job import Job
from app.models.resume import Resume
from app.nlp.diversity_analyzer import DiversityAnalyzer
from app.core.security import get_current_user

router = APIRouter(prefix="/diversity", tags=["Diversity & Inclusion"])
diversity_analyzer = DiversityAnalyzer()


@router.get("/job/{job_id}/analysis")
def get_diversity_analysis(
    job_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get diversity and inclusion analysis for a job's candidate pool.

    Args:
        job_id: Job ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Diversity analysis report

    Raises:
        HTTPException: If job not found or unauthorized
    """
    user_id = int(current_user["sub"])

    # Verify job ownership
    job = db.query(Job).filter(Job.id == job_id, Job.owner_id == user_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    # Get all resumes for this job
    resumes = db.query(Resume).filter(Resume.job_id == job_id).all()

    if not resumes:
        return diversity_analyzer._empty_report()

    # Prepare resume data
    resumes_data = []
    for resume in resumes:
        data = resume.parsed_data or {}
        data["raw_text"] = resume.raw_text
        data["total_experience_years"] = resume.total_experience_years
        resumes_data.append(data)

    # Job data
    job_data = {
        "required_skills": job.required_skills or [],
        "preferred_skills": job.preferred_skills or []
    }

    # Analyze
    analysis = diversity_analyzer.analyze_candidate_pool(resumes_data, job_data)

    return {
        "job_id": job_id,
        "job_title": job.title,
        "analysis": analysis
    }


@router.get("/portfolio/overview")
def get_portfolio_diversity(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get diversity overview across all user's job postings.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        Portfolio-wide diversity metrics
    """
    user_id = int(current_user["sub"])

    # Get all jobs
    jobs = db.query(Job).filter(Job.owner_id == user_id).all()

    if not jobs:
        return {
            "total_jobs": 0,
            "total_candidates": 0,
            "average_diversity_score": 0,
            "jobs_analysis": []
        }

    jobs_analysis = []
    total_candidates = 0
    diversity_scores = []

    for job in jobs:
        resumes = db.query(Resume).filter(Resume.job_id == job.id).all()

        if not resumes:
            continue

        total_candidates += len(resumes)

        # Prepare data
        resumes_data = []
        for resume in resumes:
            data = resume.parsed_data or {}
            data["raw_text"] = resume.raw_text
            data["total_experience_years"] = resume.total_experience_years
            resumes_data.append(data)

        # Analyze
        analysis = diversity_analyzer.analyze_candidate_pool(
            resumes_data,
            {"required_skills": job.required_skills or []}
        )

        diversity_scores.append(analysis["diversity_score"])

        jobs_analysis.append({
            "job_id": job.id,
            "job_title": job.title,
            "candidates_count": len(resumes),
            "diversity_score": analysis["diversity_score"],
            "diversity_level": analysis["education_diversity"]["diversity_level"]
        })

    avg_diversity_score = (
        sum(diversity_scores) / len(diversity_scores)
        if diversity_scores else 0
    )

    return {
        "total_jobs": len(jobs),
        "total_candidates": total_candidates,
        "average_diversity_score": round(avg_diversity_score, 2),
        "jobs_analysis": jobs_analysis
    }
