"""Ranking service for business logic."""

from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.job import Job
from app.models.resume import Resume
from app.models.ranking import Ranking
from app.nlp.ranker import ResumeRanker
from loguru import logger


class RankingService:
    """Service for ranking-related operations."""

    def __init__(self):
        """Initialize ranking service."""
        self.ranker = ResumeRanker()

    def rank_resume(self, db: Session, resume_id: int) -> Ranking:
        """Rank a single resume against its job description.

        Args:
            db: Database session
            resume_id: Resume ID

        Returns:
            Created or updated ranking

        Raises:
            ValueError: If resume or job not found
        """
        # Get resume and job
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            raise ValueError(f"Resume not found: {resume_id}")

        job = db.query(Job).filter(Job.id == resume.job_id).first()
        if not job:
            raise ValueError(f"Job not found: {resume.job_id}")

        # Prepare data for ranking
        resume_data = {
            "skills": resume.skills or [],
            "education": resume.education or [],
            "total_experience_years": resume.total_experience_years or 0.0,
        }

        job_data = {
            "required_skills": job.required_skills or [],
            "preferred_skills": job.preferred_skills or [],
            "education_level": job.education_level,
            "experience_years": job.experience_years,
        }

        # Compute ranking
        ranking_result = self.ranker.rank_resume(
            resume_data,
            job_data,
            resume.resume_embedding,
            job.description_embedding,
        )

        # Check if ranking already exists
        existing_ranking = (
            db.query(Ranking).filter(Ranking.resume_id == resume_id).first()
        )

        if existing_ranking:
            # Update existing ranking
            for key, value in ranking_result.items():
                setattr(existing_ranking, key, value)
            ranking = existing_ranking
        else:
            # Create new ranking
            ranking = Ranking(
                job_id=job.id,
                resume_id=resume.id,
                **ranking_result,
            )
            db.add(ranking)

        db.commit()
        db.refresh(ranking)

        logger.info(
            f"Ranked resume {resume_id} for job {job.id}: score={ranking.overall_score}"
        )
        return ranking

    def rank_all_resumes_for_job(self, db: Session, job_id: int) -> List[Ranking]:
        """Rank all resumes for a job.

        Args:
            db: Database session
            job_id: Job ID

        Returns:
            List of rankings

        Raises:
            ValueError: If job not found
        """
        # Check if job exists
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job not found: {job_id}")

        # Get all resumes for this job
        resumes = db.query(Resume).filter(Resume.job_id == job_id).all()

        if not resumes:
            logger.warning(f"No resumes found for job {job_id}")
            return []

        # Rank each resume
        rankings = []
        for resume in resumes:
            ranking = self.rank_resume(db, resume.id)
            rankings.append(ranking)

        # Update rank positions (sort by overall score)
        rankings.sort(key=lambda x: x.overall_score, reverse=True)
        for position, ranking in enumerate(rankings, start=1):
            ranking.rank_position = position

        db.commit()

        logger.info(f"Ranked {len(rankings)} resumes for job {job_id}")
        return rankings

    def get_rankings_for_job(
        self, db: Session, job_id: int, skip: int = 0, limit: int = 100
    ) -> List[Ranking]:
        """Get all rankings for a job, sorted by score.

        Args:
            db: Database session
            job_id: Job ID
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of rankings
        """
        return (
            db.query(Ranking)
            .filter(Ranking.job_id == job_id)
            .order_by(Ranking.overall_score.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_ranking_by_resume(self, db: Session, resume_id: int) -> Ranking:
        """Get ranking for a specific resume.

        Args:
            db: Database session
            resume_id: Resume ID

        Returns:
            Ranking or None
        """
        return db.query(Ranking).filter(Ranking.resume_id == resume_id).first()
