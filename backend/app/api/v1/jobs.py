"""Job endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.job import JobCreate, JobUpdate, JobResponse
from app.services.job_service import JobService
from app.core.security import get_current_user
from loguru import logger

router = APIRouter(prefix="/jobs", tags=["Jobs"])
job_service = JobService()


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(
    job_data: JobCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new job posting.

    Args:
        job_data: Job creation data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created job
    """
    user_id = int(current_user["sub"])
    job = job_service.create_job(db, job_data, user_id)

    # Add resume count
    response = JobResponse.from_orm(job)
    response.resume_count = job_service.get_job_resume_count(db, job.id)

    return response


@router.get("", response_model=List[JobResponse])
def get_jobs(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all jobs for current user.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of jobs
    """
    user_id = int(current_user["sub"])
    jobs = job_service.get_jobs(db, user_id, skip, limit)

    # Add resume counts
    result = []
    for job in jobs:
        job_response = JobResponse.from_orm(job)
        job_response.resume_count = job_service.get_job_resume_count(db, job.id)
        result.append(job_response)

    return result


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific job.

    Args:
        job_id: Job ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Job details

    Raises:
        HTTPException: If job not found
    """
    user_id = int(current_user["sub"])
    job = job_service.get_job(db, job_id, user_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Add resume count
    response = JobResponse.from_orm(job)
    response.resume_count = job_service.get_job_resume_count(db, job.id)

    return response


@router.put("/{job_id}", response_model=JobResponse)
def update_job(
    job_id: int,
    job_data: JobUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a job posting.

    Args:
        job_id: Job ID
        job_data: Update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated job

    Raises:
        HTTPException: If job not found
    """
    user_id = int(current_user["sub"])
    job = job_service.update_job(db, job_id, user_id, job_data)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Add resume count
    response = JobResponse.from_orm(job)
    response.resume_count = job_service.get_job_resume_count(db, job.id)

    return response


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a job posting.

    Args:
        job_id: Job ID
        current_user: Current authenticated user
        db: Database session

    Raises:
        HTTPException: If job not found
    """
    user_id = int(current_user["sub"])
    deleted = job_service.delete_job(db, job_id, user_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
