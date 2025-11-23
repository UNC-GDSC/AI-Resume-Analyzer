"""Analytics endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.job import Job
from app.models.ranking import Ranking
from app.services.ranking_service import RankingService
from app.utils.export import ExportService
from app.core.security import get_current_user
from loguru import logger

router = APIRouter(prefix="/analytics", tags=["Analytics"])
ranking_service = RankingService()
export_service = ExportService()


@router.get("/job/{job_id}/stats")
def get_job_statistics(
    job_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get analytics and statistics for a job.

    Args:
        job_id: Job ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Job statistics and analytics
    """
    user_id = int(current_user["sub"])

    # Verify job ownership
    job = db.query(Job).filter(Job.id == job_id, Job.owner_id == user_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Get all rankings
    rankings = db.query(Ranking).filter(Ranking.job_id == job_id).all()

    if not rankings:
        return {
            "job_id": job_id,
            "job_title": job.title,
            "total_candidates": 0,
            "analytics": export_service.generate_analytics_report([])
        }

    # Generate analytics
    analytics = export_service.generate_analytics_report(rankings)

    return {
        "job_id": job_id,
        "job_title": job.title,
        "total_candidates": len(rankings),
        "analytics": analytics
    }


@router.get("/job/{job_id}/export/csv")
def export_rankings_csv(
    job_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export job rankings to CSV.

    Args:
        job_id: Job ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        CSV file download
    """
    user_id = int(current_user["sub"])

    # Verify job ownership
    job = db.query(Job).filter(Job.id == job_id, Job.owner_id == user_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Get rankings with resume data
    rankings = (
        db.query(Ranking)
        .filter(Ranking.job_id == job_id)
        .order_by(Ranking.overall_score.desc())
        .all()
    )

    if not rankings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No rankings found",
        )

    # Generate CSV
    csv_content = export_service.export_rankings_to_csv(rankings, job.title)

    # Return as downloadable file
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=rankings_{job_id}.csv"
        }
    )


@router.get("/dashboard/overview")
def get_dashboard_overview(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get overview statistics for user's dashboard.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        Dashboard overview statistics
    """
    user_id = int(current_user["sub"])

    # Total jobs
    total_jobs = db.query(func.count(Job.id)).filter(Job.owner_id == user_id).scalar()

    # Total resumes across all jobs
    total_resumes = (
        db.query(func.count(Ranking.id))
        .join(Job)
        .filter(Job.owner_id == user_id)
        .scalar()
    )

    # Average score across all rankings
    avg_score = (
        db.query(func.avg(Ranking.overall_score))
        .join(Job)
        .filter(Job.owner_id == user_id)
        .scalar()
    ) or 0

    # Recent jobs
    recent_jobs = (
        db.query(Job)
        .filter(Job.owner_id == user_id)
        .order_by(Job.created_at.desc())
        .limit(5)
        .all()
    )

    # Top candidates across all jobs
    top_candidates = (
        db.query(Ranking)
        .join(Job)
        .filter(Job.owner_id == user_id)
        .order_by(Ranking.overall_score.desc())
        .limit(10)
        .all()
    )

    return {
        "total_jobs": total_jobs,
        "total_resumes": total_resumes,
        "average_score": round(float(avg_score), 2),
        "recent_jobs": [
            {
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "created_at": job.created_at
            }
            for job in recent_jobs
        ],
        "top_candidates": [
            {
                "id": ranking.id,
                "job_id": ranking.job_id,
                "candidate_name": ranking.resume.candidate_name,
                "overall_score": ranking.overall_score,
                "filename": ranking.resume.filename
            }
            for ranking in top_candidates
        ]
    }
