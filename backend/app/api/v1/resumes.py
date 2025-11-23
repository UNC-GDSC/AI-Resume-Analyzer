"""Resume endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.resume import ResumeResponse
from app.services.resume_service import ResumeService
from app.services.ranking_service import RankingService
from app.core.security import get_current_user
from loguru import logger

router = APIRouter(prefix="/resumes", tags=["Resumes"])
resume_service = ResumeService()
ranking_service = RankingService()


@router.post("/upload", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    job_id: int = Form(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload and process a resume.

    Args:
        file: Resume file (PDF, DOCX, or TXT)
        job_id: Associated job ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Processed resume

    Raises:
        HTTPException: If processing fails
    """
    try:
        # Process resume
        resume = await resume_service.process_resume(db, file, job_id)

        # Automatically rank the resume
        ranking_service.rank_resume(db, resume.id)

        logger.info(f"Uploaded and ranked resume: {resume.filename}")
        return resume

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error uploading resume: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process resume",
        )


@router.get("/job/{job_id}", response_model=List[ResumeResponse])
def get_resumes_by_job(
    job_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all resumes for a job.

    Args:
        job_id: Job ID
        skip: Number of records to skip
        limit: Maximum number of records
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of resumes
    """
    resumes = resume_service.get_resumes_by_job(db, job_id, skip, limit)
    return resumes


@router.get("/{resume_id}", response_model=ResumeResponse)
def get_resume(
    resume_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific resume.

    Args:
        resume_id: Resume ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Resume details

    Raises:
        HTTPException: If resume not found
    """
    resume = resume_service.get_resume(db, resume_id)

    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found",
        )

    return resume


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resume(
    resume_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a resume.

    Args:
        resume_id: Resume ID
        current_user: Current authenticated user
        db: Database session

    Raises:
        HTTPException: If resume not found
    """
    deleted = resume_service.delete_resume(db, resume_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found",
        )
