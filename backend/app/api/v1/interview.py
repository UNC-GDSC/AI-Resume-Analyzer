"""Advanced interview endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.resume import Resume
from app.models.job import Job
from app.nlp.interview_generator import InterviewQuestionGenerator
from app.core.security import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/interview", tags=["Interview"])
question_generator = InterviewQuestionGenerator()


class InterviewQuestionResponse(BaseModel):
    """Interview question response model."""
    number: int
    category: str
    question: str
    difficulty: str
    focus_area: str
    why_asked: str


class InterviewScorecardResponse(BaseModel):
    """Interview scorecard response model."""
    candidate_info: dict
    questions: List[dict]
    overall_assessment: dict


@router.get("/questions/resume/{resume_id}", response_model=List[InterviewQuestionResponse])
def generate_interview_questions(
    resume_id: int,
    num_questions: int = 15,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate personalized interview questions for a resume.

    Args:
        resume_id: Resume ID
        num_questions: Number of questions to generate (default: 15)
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of interview questions

    Raises:
        HTTPException: If resume not found
    """
    # Get resume and job
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )

    job = db.query(Job).filter(Job.id == resume.job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    # Verify ownership
    user_id = int(current_user["sub"])
    if job.owner_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this resource"
        )

    # Generate questions
    resume_data = resume.parsed_data or {}
    job_data = {
        "required_skills": job.required_skills or [],
        "preferred_skills": job.preferred_skills or [],
        "experience_years": job.experience_years,
        "education_level": job.education_level
    }

    questions = question_generator.generate_questions(
        resume_data, job_data, num_questions
    )

    return questions


@router.get("/scorecard/resume/{resume_id}", response_model=InterviewScorecardResponse)
def generate_interview_scorecard(
    resume_id: int,
    num_questions: int = 15,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate interview scorecard template.

    Args:
        resume_id: Resume ID
        num_questions: Number of questions (default: 15)
        current_user: Current authenticated user
        db: Database session

    Returns:
        Interview scorecard template

    Raises:
        HTTPException: If resume not found
    """
    # Get resume and job
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )

    job = db.query(Job).filter(Job.id == resume.job_id).first()

    # Verify ownership
    user_id = int(current_user["sub"])
    if job.owner_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )

    # Generate questions
    resume_data = resume.parsed_data or {}
    job_data = {
        "required_skills": job.required_skills or [],
        "preferred_skills": job.preferred_skills or [],
    }

    questions = question_generator.generate_questions(
        resume_data, job_data, num_questions
    )

    # Generate scorecard
    scorecard = question_generator.generate_question_scorecard(questions)

    # Add candidate info
    scorecard["candidate_info"]["name"] = resume.candidate_name or "Unknown"
    scorecard["candidate_info"]["position"] = job.title

    return scorecard
