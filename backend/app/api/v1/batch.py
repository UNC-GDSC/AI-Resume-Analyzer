"""Batch processing endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.resume_service import ResumeService
from app.services.ranking_service import RankingService
from app.utils.email import EmailService
from app.core.security import get_current_user
from loguru import logger
import asyncio

router = APIRouter(prefix="/batch", tags=["Batch Processing"])
resume_service = ResumeService()
ranking_service = RankingService()
email_service = EmailService()


@router.post("/upload/{job_id}")
async def batch_upload_resumes(
    job_id: int,
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload multiple resumes at once.

    Args:
        job_id: Job ID
        files: List of resume files
        current_user: Current authenticated user
        db: Database session

    Returns:
        Batch upload results
    """
    results = {
        "total": len(files),
        "successful": 0,
        "failed": 0,
        "results": []
    }

    for file in files:
        try:
            # Process resume
            resume = await resume_service.process_resume(db, file, job_id)

            # Rank resume
            ranking_service.rank_resume(db, resume.id)

            results["successful"] += 1
            results["results"].append({
                "filename": file.filename,
                "status": "success",
                "resume_id": resume.id
            })

            logger.info(f"Batch processed: {file.filename}")

        except Exception as e:
            results["failed"] += 1
            results["results"].append({
                "filename": file.filename,
                "status": "failed",
                "error": str(e)
            })
            logger.error(f"Batch processing failed for {file.filename}: {str(e)}")

    # Send email notification (optional)
    user = current_user.get("username", "")
    if user and results["total"] > 0:
        # This would require user email in the token or database lookup
        # email_service.send_batch_upload_notification(
        #     user_email, job_title, results["successful"], results["failed"]
        # )
        pass

    return results


@router.post("/rerank-all")
async def batch_rerank_all_jobs(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Re-rank all resumes for all user's jobs.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        Batch rerank results
    """
    user_id = int(current_user["sub"])

    from app.models.job import Job

    jobs = db.query(Job).filter(Job.owner_id == user_id).all()

    results = {
        "total_jobs": len(jobs),
        "successful": 0,
        "failed": 0,
        "details": []
    }

    for job in jobs:
        try:
            rankings = ranking_service.rank_all_resumes_for_job(db, job.id)
            results["successful"] += 1
            results["details"].append({
                "job_id": job.id,
                "job_title": job.title,
                "status": "success",
                "rankings_count": len(rankings)
            })
        except Exception as e:
            results["failed"] += 1
            results["details"].append({
                "job_id": job.id,
                "job_title": job.title,
                "status": "failed",
                "error": str(e)
            })

    return results
