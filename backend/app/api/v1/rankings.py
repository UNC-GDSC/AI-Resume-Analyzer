"""Ranking endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.ranking import RankingResponse
from app.services.ranking_service import RankingService
from app.services.resume_service import ResumeService
from app.core.security import get_current_user
from loguru import logger

router = APIRouter(prefix="/rankings", tags=["Rankings"])
ranking_service = RankingService()
resume_service = ResumeService()


@router.get("/job/{job_id}", response_model=List[RankingResponse])
def get_job_rankings(
    job_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all rankings for a job, sorted by score.

    Args:
        job_id: Job ID
        skip: Number of records to skip
        limit: Maximum number of records
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of rankings with resume details
    """
    rankings = ranking_service.get_rankings_for_job(db, job_id, skip, limit)

    # Enrich with resume data
    result = []
    for ranking in rankings:
        resume = resume_service.get_resume(db, ranking.resume_id)
        ranking_dict = {
            "id": ranking.id,
            "job_id": ranking.job_id,
            "resume_id": ranking.resume_id,
            "overall_score": ranking.overall_score,
            "semantic_similarity_score": ranking.semantic_similarity_score,
            "skill_match_score": ranking.skill_match_score,
            "experience_score": ranking.experience_score,
            "education_score": ranking.education_score,
            "matched_skills": ranking.matched_skills,
            "missing_skills": ranking.missing_skills,
            "summary": ranking.summary,
            "strengths": ranking.strengths,
            "weaknesses": ranking.weaknesses,
            "rank_position": ranking.rank_position,
            "candidate_name": resume.candidate_name if resume else None,
            "candidate_email": resume.email if resume else None,
            "filename": resume.filename if resume else "Unknown",
            "created_at": ranking.created_at,
        }
        result.append(RankingResponse(**ranking_dict))

    return result


@router.post("/job/{job_id}/rerank", response_model=List[RankingResponse])
def rerank_job(
    job_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Re-rank all resumes for a job.

    Args:
        job_id: Job ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated rankings

    Raises:
        HTTPException: If job not found or ranking fails
    """
    try:
        rankings = ranking_service.rank_all_resumes_for_job(db, job_id)

        # Enrich with resume data
        result = []
        for ranking in rankings:
            resume = resume_service.get_resume(db, ranking.resume_id)
            ranking_dict = {
                "id": ranking.id,
                "job_id": ranking.job_id,
                "resume_id": ranking.resume_id,
                "overall_score": ranking.overall_score,
                "semantic_similarity_score": ranking.semantic_similarity_score,
                "skill_match_score": ranking.skill_match_score,
                "experience_score": ranking.experience_score,
                "education_score": ranking.education_score,
                "matched_skills": ranking.matched_skills,
                "missing_skills": ranking.missing_skills,
                "summary": ranking.summary,
                "strengths": ranking.strengths,
                "weaknesses": ranking.weaknesses,
                "rank_position": ranking.rank_position,
                "candidate_name": resume.candidate_name if resume else None,
                "candidate_email": resume.email if resume else None,
                "filename": resume.filename if resume else "Unknown",
                "created_at": ranking.created_at,
            }
            result.append(RankingResponse(**ranking_dict))

        logger.info(f"Re-ranked {len(result)} resumes for job {job_id}")
        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error re-ranking job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to rank resumes",
        )


@router.get("/resume/{resume_id}", response_model=RankingResponse)
def get_resume_ranking(
    resume_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get ranking for a specific resume.

    Args:
        resume_id: Resume ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Ranking details

    Raises:
        HTTPException: If ranking not found
    """
    ranking = ranking_service.get_ranking_by_resume(db, resume_id)

    if not ranking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ranking not found",
        )

    # Enrich with resume data
    resume = resume_service.get_resume(db, resume_id)
    ranking_dict = {
        "id": ranking.id,
        "job_id": ranking.job_id,
        "resume_id": ranking.resume_id,
        "overall_score": ranking.overall_score,
        "semantic_similarity_score": ranking.semantic_similarity_score,
        "skill_match_score": ranking.skill_match_score,
        "experience_score": ranking.experience_score,
        "education_score": ranking.education_score,
        "matched_skills": ranking.matched_skills,
        "missing_skills": ranking.missing_skills,
        "summary": ranking.summary,
        "strengths": ranking.strengths,
        "weaknesses": ranking.weaknesses,
        "rank_position": ranking.rank_position,
        "candidate_name": resume.candidate_name if resume else None,
        "candidate_email": resume.email if resume else None,
        "filename": resume.filename if resume else "Unknown",
        "created_at": ranking.created_at,
    }

    return RankingResponse(**ranking_dict)
