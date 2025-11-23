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
from app.utils.pdf_generator import PDFReportGenerator
from app.core.security import get_current_user
from app.ml.predictive import PredictiveAnalyzer
from app.ml.skill_gap import SkillGapAnalyzer
from app.nlp.quality_analyzer import QualityAnalyzer
from loguru import logger

router = APIRouter(prefix="/analytics", tags=["Analytics"])
ranking_service = RankingService()
export_service = ExportService()
pdf_generator = PDFReportGenerator()
predictive_analyzer = PredictiveAnalyzer()
skill_gap_analyzer = SkillGapAnalyzer()
quality_analyzer = QualityAnalyzer()


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


@router.get("/job/{job_id}/export/pdf/candidate/{ranking_id}")
def export_candidate_pdf(
    job_id: int,
    ranking_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export comprehensive candidate analysis as PDF report.

    Args:
        job_id: Job ID
        ranking_id: Ranking ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        PDF file download
    """
    user_id = int(current_user["sub"])

    # Verify job ownership
    job = db.query(Job).filter(Job.id == job_id, Job.owner_id == user_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Get ranking with resume
    ranking = (
        db.query(Ranking)
        .filter(Ranking.id == ranking_id, Ranking.job_id == job_id)
        .first()
    )

    if not ranking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ranking not found",
        )

    # Prepare data for PDF
    candidate_data = {
        "filename": ranking.resume.filename if ranking.resume else "Unknown",
        "candidate_name": ranking.resume.candidate_name if ranking.resume else "Unknown"
    }

    ranking_data = {
        "overall_score": ranking.overall_score,
        "semantic_similarity_score": ranking.semantic_similarity_score,
        "skill_match_score": ranking.skill_match_score,
        "experience_score": ranking.experience_score,
        "education_score": ranking.education_score,
        "matched_skills": ranking.matched_skills or [],
        "missing_skills": ranking.missing_skills or []
    }

    job_data = {
        "title": job.title,
        "company": job.company if hasattr(job, 'company') else "Company",
        "description": job.description
    }

    # Get skill gap analysis
    try:
        parsed_data = ranking.resume.parsed_data or {}
        candidate_skills = parsed_data.get("skills", [])
        job_requirements = {
            "required_skills": job.required_skills or [],
            "preferred_skills": job.preferred_skills or []
        }
        skill_gap_analysis = skill_gap_analyzer.analyze_individual_gap(
            candidate_skills,
            job_requirements
        )
    except Exception as e:
        logger.warning(f"Could not generate skill gap analysis: {str(e)}")
        skill_gap_analysis = None

    # Get quality analysis
    try:
        quality_analysis = quality_analyzer.analyze_resume_quality(
            ranking.resume.file_content or "",
            ranking.resume.parsed_data or {}
        )
    except Exception as e:
        logger.warning(f"Could not generate quality analysis: {str(e)}")
        quality_analysis = None

    # Generate PDF
    try:
        pdf_buffer = pdf_generator.generate_candidate_report(
            candidate_data,
            ranking_data,
            job_data,
            skill_gap_analysis,
            quality_analysis
        )

        logger.info(f"Generated PDF report for ranking {ranking_id}")

        return Response(
            content=pdf_buffer.read(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=candidate_report_{ranking_id}.pdf"
            }
        )

    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF report: {str(e)}"
        )


@router.get("/job/{job_id}/export/pdf/pool")
def export_pool_summary_pdf(
    job_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export pool summary report as PDF.

    Args:
        job_id: Job ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        PDF file download
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
    rankings = (
        db.query(Ranking)
        .filter(Ranking.job_id == job_id)
        .order_by(Ranking.overall_score.desc())
        .all()
    )

    if not rankings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No candidates found for this job",
        )

    # Prepare data
    job_data = {
        "title": job.title,
        "company": job.company if hasattr(job, 'company') else "Company",
        "description": job.description
    }

    ranking_data = [
        {
            "overall_score": r.overall_score,
            "skill_match_score": r.skill_match_score,
            "experience_score": r.experience_score,
            "education_score": r.education_score,
            "resume_filename": r.resume.filename if r.resume else "Unknown",
            "matched_skills": r.matched_skills or [],
            "missing_skills": r.missing_skills or []
        }
        for r in rankings
    ]

    # Get pool quality analysis
    try:
        job_requirements = {
            "required_skills": job.required_skills or [],
            "experience_years": job.experience_years or 0
        }
        pool_quality = predictive_analyzer.analyze_candidate_pool_quality(
            ranking_data,
            job_requirements
        )
    except Exception as e:
        logger.warning(f"Could not generate pool quality analysis: {str(e)}")
        pool_quality = {"quality_tier": "N/A", "quality_description": "Analysis unavailable"}

    # Generate PDF
    try:
        pdf_buffer = pdf_generator.generate_pool_summary_report(
            job_data,
            ranking_data,
            pool_quality
        )

        logger.info(f"Generated pool summary PDF for job {job_id}")

        return Response(
            content=pdf_buffer.read(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=pool_summary_{job_id}.pdf"
            }
        )

    except Exception as e:
        logger.error(f"Error generating pool PDF: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate pool summary PDF: {str(e)}"
        )
