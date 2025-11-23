"""ML-powered features API endpoints."""

from typing import List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from loguru import logger

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.resume import Resume
from app.models.job import Job
from app.models.ranking import Ranking
from app.ml.predictive import PredictiveAnalyzer
from app.ml.anonymizer import ResumeAnonymizer
from app.ml.skill_gap import SkillGapAnalyzer

router = APIRouter()

# Initialize ML components
predictive_analyzer = PredictiveAnalyzer()
anonymizer = ResumeAnonymizer()
skill_gap_analyzer = SkillGapAnalyzer()


@router.post("/predict-success/{ranking_id}", response_model=Dict)
async def predict_hiring_success(
    ranking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Predict hiring success probability for a ranked candidate.

    Args:
        ranking_id: ID of the ranking to analyze

    Returns:
        Prediction with success probability, risk factors, and recommendations
    """
    try:
        # Get ranking
        ranking = db.query(Ranking).filter(
            Ranking.id == ranking_id,
            Ranking.job.has(user_id=current_user.id)
        ).first()

        if not ranking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ranking not found"
            )

        # Prepare features
        ranking_features = {
            "overall_score": ranking.overall_score,
            "semantic_similarity_score": ranking.semantic_similarity_score,
            "skill_match_score": ranking.skill_match_score,
            "experience_score": ranking.experience_score,
            "education_score": ranking.education_score,
            "matched_skills": ranking.matched_skills or [],
            "missing_skills": ranking.missing_skills or []
        }

        # Predict
        prediction = predictive_analyzer.predict_hiring_success(ranking_features)

        logger.info(f"Predicted hiring success for ranking {ranking_id}: {prediction['success_probability']}")

        return {
            "ranking_id": ranking_id,
            "resume_id": ranking.resume_id,
            "job_id": ranking.job_id,
            "prediction": prediction
        }

    except Exception as e:
        logger.error(f"Error predicting hiring success: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to predict hiring success: {str(e)}"
        )


@router.post("/predict-time-to-hire/{job_id}", response_model=Dict)
async def predict_time_to_hire(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Predict time to hire for a job position.

    Args:
        job_id: ID of the job

    Returns:
        Time to hire prediction with confidence range
    """
    try:
        # Get job
        job = db.query(Job).filter(
            Job.id == job_id,
            Job.user_id == current_user.id
        ).first()

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )

        # Prepare job features
        job_features = {
            "experience_years": job.experience_years or 3,
            "required_skills": job.required_skills or [],
            "job_level": job.job_level if hasattr(job, 'job_level') else None
        }

        # Predict
        prediction = predictive_analyzer.predict_time_to_hire(job_features)

        logger.info(f"Predicted time to hire for job {job_id}: {prediction['predicted_days']} days")

        return {
            "job_id": job_id,
            "job_title": job.title,
            "prediction": prediction
        }

    except Exception as e:
        logger.error(f"Error predicting time to hire: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to predict time to hire: {str(e)}"
        )


@router.get("/pool-quality/{job_id}", response_model=Dict)
async def analyze_pool_quality(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Analyze overall quality of candidate pool for a job.

    Args:
        job_id: ID of the job

    Returns:
        Comprehensive pool quality analysis with recommendations
    """
    try:
        # Get job
        job = db.query(Job).filter(
            Job.id == job_id,
            Job.user_id == current_user.id
        ).first()

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )

        # Get all rankings for this job
        rankings = db.query(Ranking).filter(
            Ranking.job_id == job_id
        ).all()

        # Prepare ranking data
        ranking_data = [
            {
                "overall_score": r.overall_score,
                "skill_match_score": r.skill_match_score,
                "experience_score": r.experience_score,
                "education_score": r.education_score,
                "matched_skills": r.matched_skills or [],
                "missing_skills": r.missing_skills or []
            }
            for r in rankings
        ]

        # Prepare job requirements
        job_requirements = {
            "required_skills": job.required_skills or [],
            "experience_years": job.experience_years or 0
        }

        # Analyze pool quality
        analysis = predictive_analyzer.analyze_candidate_pool_quality(
            ranking_data,
            job_requirements
        )

        logger.info(f"Analyzed pool quality for job {job_id}: {analysis.get('quality_tier', 'N/A')}")

        return {
            "job_id": job_id,
            "job_title": job.title,
            "analysis": analysis
        }

    except Exception as e:
        logger.error(f"Error analyzing pool quality: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze pool quality: {str(e)}"
        )


@router.post("/anonymize/{resume_id}", response_model=Dict)
async def anonymize_resume(
    resume_id: int,
    anonymization_level: str = "standard",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Anonymize a resume to reduce unconscious bias.

    Args:
        resume_id: ID of the resume to anonymize
        anonymization_level: Level of anonymization (minimal, standard, maximum)

    Returns:
        Anonymized resume with change log
    """
    try:
        # Validate level
        if anonymization_level not in ["minimal", "standard", "maximum"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid anonymization level. Must be: minimal, standard, or maximum"
            )

        # Get resume (check ownership via job)
        resume = db.query(Resume).join(Job).filter(
            Resume.id == resume_id,
            Job.user_id == current_user.id
        ).first()

        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found"
            )

        # Anonymize
        result = anonymizer.anonymize_resume(
            resume.file_content or "",
            resume.parsed_data or {},
            anonymization_level
        )

        logger.info(f"Anonymized resume {resume_id} with level '{anonymization_level}': {result['changes_made']} changes")

        return {
            "resume_id": resume_id,
            "original_filename": resume.filename,
            "anonymization_result": result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error anonymizing resume: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to anonymize resume: {str(e)}"
        )


@router.get("/bias-report/{resume_id}", response_model=Dict)
async def get_bias_report(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate bias indicator report for a resume.

    Args:
        resume_id: ID of the resume to analyze

    Returns:
        Bias risk assessment and anonymization recommendations
    """
    try:
        # Get resume (check ownership via job)
        resume = db.query(Resume).join(Job).filter(
            Resume.id == resume_id,
            Job.user_id == current_user.id
        ).first()

        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found"
            )

        # Generate bias report
        report = anonymizer.get_bias_report(
            resume.file_content or "",
            resume.parsed_data or {}
        )

        logger.info(f"Generated bias report for resume {resume_id}: {report['bias_risk_level']} risk")

        return {
            "resume_id": resume_id,
            "original_filename": resume.filename,
            "bias_report": report
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating bias report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate bias report: {str(e)}"
        )


@router.get("/skill-gaps/pool/{job_id}", response_model=Dict)
async def analyze_pool_skill_gaps(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Analyze skill gaps across entire candidate pool.

    Args:
        job_id: ID of the job

    Returns:
        Pool-wide skill gap analysis with sourcing strategy
    """
    try:
        # Get job
        job = db.query(Job).filter(
            Job.id == job_id,
            Job.user_id == current_user.id
        ).first()

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )

        # Get all resumes for this job
        resumes = db.query(Resume).filter(
            Resume.job_id == job_id
        ).all()

        # Prepare candidates data
        candidates_data = [
            resume.parsed_data or {}
            for resume in resumes
        ]

        # Prepare job requirements
        job_requirements = {
            "required_skills": job.required_skills or [],
            "preferred_skills": job.preferred_skills or []
        }

        # Analyze gaps
        analysis = skill_gap_analyzer.analyze_candidate_pool_gaps(
            candidates_data,
            job_requirements
        )

        logger.info(f"Analyzed pool skill gaps for job {job_id}: {len(analysis['gaps']['critical'])} critical gaps")

        return {
            "job_id": job_id,
            "job_title": job.title,
            "skill_gap_analysis": analysis
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing pool skill gaps: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze pool skill gaps: {str(e)}"
        )


@router.get("/skill-gaps/candidate/{resume_id}", response_model=Dict)
async def analyze_individual_skill_gaps(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Analyze skill gaps for individual candidate with learning paths.

    Args:
        resume_id: ID of the resume to analyze

    Returns:
        Individual skill gap analysis with learning paths and trainability assessment
    """
    try:
        # Get resume with job (check ownership)
        resume = db.query(Resume).join(Job).filter(
            Resume.id == resume_id,
            Job.user_id == current_user.id
        ).first()

        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found"
            )

        # Get candidate skills
        parsed_data = resume.parsed_data or {}
        candidate_skills = parsed_data.get("skills", [])

        # Get job requirements
        job = resume.job
        job_requirements = {
            "required_skills": job.required_skills or [],
            "preferred_skills": job.preferred_skills or []
        }

        # Analyze individual gaps
        analysis = skill_gap_analyzer.analyze_individual_gap(
            candidate_skills,
            job_requirements
        )

        logger.info(
            f"Analyzed individual skill gaps for resume {resume_id}: "
            f"{analysis['gaps']['missing_required_count']} missing required skills"
        )

        return {
            "resume_id": resume_id,
            "job_id": job.id,
            "job_title": job.title,
            "candidate_filename": resume.filename,
            "skill_gap_analysis": analysis
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing individual skill gaps: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze individual skill gaps: {str(e)}"
        )


@router.post("/batch-predict-success/{job_id}", response_model=Dict)
async def batch_predict_hiring_success(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Predict hiring success for all candidates in a job.

    Args:
        job_id: ID of the job

    Returns:
        Batch predictions for all ranked candidates
    """
    try:
        # Get job
        job = db.query(Job).filter(
            Job.id == job_id,
            Job.user_id == current_user.id
        ).first()

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )

        # Get all rankings for this job
        rankings = db.query(Ranking).filter(
            Ranking.job_id == job_id
        ).all()

        # Predict for each ranking
        predictions = []
        for ranking in rankings:
            ranking_features = {
                "overall_score": ranking.overall_score,
                "semantic_similarity_score": ranking.semantic_similarity_score,
                "skill_match_score": ranking.skill_match_score,
                "experience_score": ranking.experience_score,
                "education_score": ranking.education_score,
                "matched_skills": ranking.matched_skills or [],
                "missing_skills": ranking.missing_skills or []
            }

            prediction = predictive_analyzer.predict_hiring_success(ranking_features)

            predictions.append({
                "ranking_id": ranking.id,
                "resume_id": ranking.resume_id,
                "resume_filename": ranking.resume.filename if ranking.resume else "Unknown",
                "overall_score": ranking.overall_score,
                "prediction": prediction
            })

        # Sort by success probability
        predictions.sort(key=lambda x: x["prediction"]["success_probability"], reverse=True)

        logger.info(f"Batch predicted hiring success for {len(predictions)} candidates in job {job_id}")

        return {
            "job_id": job_id,
            "job_title": job.title,
            "total_candidates": len(predictions),
            "predictions": predictions,
            "summary": {
                "high_probability": len([p for p in predictions if p["prediction"]["success_probability"] >= 0.75]),
                "moderate_probability": len([p for p in predictions if 0.45 <= p["prediction"]["success_probability"] < 0.75]),
                "low_probability": len([p for p in predictions if p["prediction"]["success_probability"] < 0.45])
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch prediction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to batch predict: {str(e)}"
        )
