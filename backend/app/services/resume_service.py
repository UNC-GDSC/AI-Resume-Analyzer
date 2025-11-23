"""Resume service for business logic."""

import os
import shutil
from pathlib import Path
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import UploadFile
from app.models.resume import Resume
from app.models.job import Job
from app.nlp.text_extractor import TextExtractor
from app.nlp.resume_parser import ResumeParser
from app.nlp.ranker import ResumeRanker
from app.core.config import settings
from loguru import logger


class ResumeService:
    """Service for resume-related operations."""

    def __init__(self):
        """Initialize resume service."""
        self.text_extractor = TextExtractor()
        self.resume_parser = ResumeParser()
        self.ranker = ResumeRanker()

        # Ensure upload directory exists
        Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

    def validate_file(self, file: UploadFile) -> bool:
        """Validate uploaded file.

        Args:
            file: Uploaded file

        Returns:
            True if valid, False otherwise

        Raises:
            ValueError: If validation fails
        """
        # Check file extension
        extension = Path(file.filename).suffix.lower().replace(".", "")
        if extension not in settings.allowed_extensions_list:
            raise ValueError(
                f"Invalid file type. Allowed: {', '.join(settings.allowed_extensions_list)}"
            )

        # Check file size (if we can determine it)
        if hasattr(file, 'size') and file.size > settings.MAX_FILE_SIZE:
            raise ValueError(
                f"File too large. Maximum size: {settings.MAX_FILE_SIZE / 1024 / 1024}MB"
            )

        return True

    async def save_file(self, file: UploadFile, job_id: int) -> str:
        """Save uploaded file to disk.

        Args:
            file: Uploaded file
            job_id: Associated job ID

        Returns:
            File path

        Raises:
            Exception: If file save fails
        """
        try:
            # Create job-specific directory
            job_dir = Path(settings.UPLOAD_DIR) / str(job_id)
            job_dir.mkdir(parents=True, exist_ok=True)

            # Generate unique filename
            timestamp = int(Path(file.filename).stem.split("_")[-1]) if "_" in file.filename else 0
            safe_filename = f"{timestamp}_{file.filename}"
            file_path = job_dir / safe_filename

            # Save file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            logger.info(f"Saved file: {file_path}")
            return str(file_path)

        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            raise

    async def process_resume(
        self, db: Session, file: UploadFile, job_id: int
    ) -> Resume:
        """Process uploaded resume file.

        Args:
            db: Database session
            file: Uploaded file
            job_id: Associated job ID

        Returns:
            Created resume record

        Raises:
            ValueError: If validation fails
            Exception: If processing fails
        """
        # Validate file
        self.validate_file(file)

        # Check if job exists
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job not found: {job_id}")

        # Save file
        file_path = await self.save_file(file, job_id)

        try:
            # Extract text
            raw_text = self.text_extractor.extract_text(file_path)
            cleaned_text = self.text_extractor.clean_text(raw_text)

            # Parse resume
            parsed_data = self.resume_parser.parse(cleaned_text)

            # Compute resume embedding
            resume_embedding = self.ranker.compute_embedding(cleaned_text)

            # Create resume record
            resume = Resume(
                filename=file.filename,
                file_path=file_path,
                file_type=Path(file.filename).suffix.lower().replace(".", ""),
                raw_text=raw_text,
                parsed_data=parsed_data,
                candidate_name=parsed_data.get("name"),
                email=parsed_data.get("email"),
                phone=parsed_data.get("phone"),
                skills=parsed_data.get("skills", []),
                education=parsed_data.get("education", []),
                experience=parsed_data.get("experience", []),
                total_experience_years=parsed_data.get("total_experience_years", 0.0),
                resume_embedding=resume_embedding,
                job_id=job_id,
            )

            db.add(resume)
            db.commit()
            db.refresh(resume)

            logger.info(
                f"Processed resume: {resume.filename} (ID: {resume.id}) for job {job_id}"
            )
            return resume

        except Exception as e:
            # Clean up file if processing fails
            if os.path.exists(file_path):
                os.remove(file_path)
            logger.error(f"Error processing resume: {str(e)}")
            raise

    def get_resume(self, db: Session, resume_id: int) -> Optional[Resume]:
        """Get a resume by ID.

        Args:
            db: Database session
            resume_id: Resume ID

        Returns:
            Resume or None
        """
        return db.query(Resume).filter(Resume.id == resume_id).first()

    def get_resumes_by_job(
        self, db: Session, job_id: int, skip: int = 0, limit: int = 100
    ) -> List[Resume]:
        """Get all resumes for a job.

        Args:
            db: Database session
            job_id: Job ID
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of resumes
        """
        return (
            db.query(Resume)
            .filter(Resume.job_id == job_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def delete_resume(self, db: Session, resume_id: int) -> bool:
        """Delete a resume.

        Args:
            db: Database session
            resume_id: Resume ID

        Returns:
            True if deleted, False otherwise
        """
        resume = self.get_resume(db, resume_id)
        if not resume:
            return False

        # Delete file
        if os.path.exists(resume.file_path):
            os.remove(resume.file_path)

        db.delete(resume)
        db.commit()

        logger.info(f"Deleted resume: {resume.filename} (ID: {resume.id})")
        return True
