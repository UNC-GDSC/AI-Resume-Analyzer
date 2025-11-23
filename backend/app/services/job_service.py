"""Job service for business logic."""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.job import Job
from app.models.resume import Resume
from app.schemas.job import JobCreate, JobUpdate
from app.nlp.job_parser import JobParser
from app.nlp.ranker import ResumeRanker
from loguru import logger


class JobService:
    """Service for job-related operations."""

    def __init__(self):
        """Initialize job service."""
        self.job_parser = JobParser()
        self.ranker = ResumeRanker()

    def create_job(self, db: Session, job_data: JobCreate, owner_id: int) -> Job:
        """Create a new job posting.

        Args:
            db: Database session
            job_data: Job creation data
            owner_id: Owner user ID

        Returns:
            Created job
        """
        # Parse job description
        parsed_data = self.job_parser.parse(job_data.title, job_data.description)

        # Compute job description embedding
        full_description = f"{job_data.title}\n{job_data.description}"
        if job_data.requirements:
            full_description += f"\n{job_data.requirements}"

        job_embedding = self.ranker.compute_embedding(full_description)

        # Create job
        job = Job(
            title=job_data.title,
            description=job_data.description,
            requirements=job_data.requirements,
            company=job_data.company,
            location=job_data.location,
            owner_id=owner_id,
            required_skills=parsed_data["required_skills"],
            preferred_skills=parsed_data["preferred_skills"],
            education_level=parsed_data["education_level"],
            experience_years=parsed_data["experience_years"],
            description_embedding=job_embedding,
        )

        db.add(job)
        db.commit()
        db.refresh(job)

        logger.info(f"Created job: {job.title} (ID: {job.id})")
        return job

    def get_job(self, db: Session, job_id: int, owner_id: int) -> Optional[Job]:
        """Get a job by ID.

        Args:
            db: Database session
            job_id: Job ID
            owner_id: Owner user ID

        Returns:
            Job or None
        """
        return db.query(Job).filter(Job.id == job_id, Job.owner_id == owner_id).first()

    def get_jobs(self, db: Session, owner_id: int, skip: int = 0, limit: int = 100) -> List[Job]:
        """Get all jobs for a user.

        Args:
            db: Database session
            owner_id: Owner user ID
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of jobs
        """
        return db.query(Job).filter(Job.owner_id == owner_id).offset(skip).limit(limit).all()

    def update_job(
        self, db: Session, job_id: int, owner_id: int, job_data: JobUpdate
    ) -> Optional[Job]:
        """Update a job posting.

        Args:
            db: Database session
            job_id: Job ID
            owner_id: Owner user ID
            job_data: Update data

        Returns:
            Updated job or None
        """
        job = self.get_job(db, job_id, owner_id)
        if not job:
            return None

        # Update fields
        update_data = job_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(job, field, value)

        # Re-parse if description changed
        if "title" in update_data or "description" in update_data:
            parsed_data = self.job_parser.parse(job.title, job.description)
            job.required_skills = parsed_data["required_skills"]
            job.preferred_skills = parsed_data["preferred_skills"]
            job.education_level = parsed_data["education_level"]
            job.experience_years = parsed_data["experience_years"]

            # Recompute embedding
            full_description = f"{job.title}\n{job.description}"
            if job.requirements:
                full_description += f"\n{job.requirements}"
            job.description_embedding = self.ranker.compute_embedding(full_description)

        db.commit()
        db.refresh(job)

        logger.info(f"Updated job: {job.title} (ID: {job.id})")
        return job

    def delete_job(self, db: Session, job_id: int, owner_id: int) -> bool:
        """Delete a job posting.

        Args:
            db: Database session
            job_id: Job ID
            owner_id: Owner user ID

        Returns:
            True if deleted, False otherwise
        """
        job = self.get_job(db, job_id, owner_id)
        if not job:
            return False

        db.delete(job)
        db.commit()

        logger.info(f"Deleted job: {job.title} (ID: {job.id})")
        return True

    def get_job_resume_count(self, db: Session, job_id: int) -> int:
        """Get count of resumes for a job.

        Args:
            db: Database session
            job_id: Job ID

        Returns:
            Resume count
        """
        return db.query(Resume).filter(Resume.job_id == job_id).count()
