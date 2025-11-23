"""Candidate self-service portal API endpoints."""

from typing import Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from loguru import logger

from app.core.database import get_db
from app.models.resume import Resume
from app.models.ranking import Ranking
from app.models.job import Job
from app.ml.skill_gap import SkillGapAnalyzer
from app.nlp.quality_analyzer import QualityAnalyzer
from app.ml.anonymizer import ResumeAnonymizer

router = APIRouter()

# Initialize components
skill_gap_analyzer = SkillGapAnalyzer()
quality_analyzer = QualityAnalyzer()
anonymizer = ResumeAnonymizer()


def verify_candidate_token(token: str, db: Session) -> Optional[Resume]:
    """Verify candidate access token and return resume.

    Args:
        token: Unique access token for the resume
        db: Database session

    Returns:
        Resume if token is valid, None otherwise
    """
    # Token format: resume_id encoded (for simplicity using resume_id directly)
    # In production, use JWT or encrypted tokens
    try:
        resume_id = int(token)
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        return resume
    except (ValueError, TypeError):
        return None


@router.get("/access/{token}", response_model=Dict)
async def get_candidate_dashboard(
    token: str,
    db: Session = Depends(get_db)
):
    """Get candidate's personalized dashboard.

    Args:
        token: Candidate access token

    Returns:
        Dashboard with rankings, feedback, and recommendations
    """
    try:
        # Verify token
        resume = verify_candidate_token(token, db)
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid access token"
            )

        # Get job information
        job = resume.job

        # Get ranking
        ranking = db.query(Ranking).filter(
            Ranking.resume_id == resume.id,
            Ranking.job_id == job.id
        ).first()

        if not ranking:
            return {
                "resume_id": resume.id,
                "job_title": job.title,
                "status": "processing",
                "message": "Your application is being processed"
            }

        # Build dashboard data
        dashboard = {
            "candidate_info": {
                "resume_id": resume.id,
                "filename": resume.filename,
                "submitted_at": resume.created_at.isoformat() if resume.created_at else None,
                "status": "ranked"
            },
            "job_info": {
                "title": job.title,
                "company": job.company if hasattr(job, 'company') else "Company",
                "description": job.description[:200] + "..." if len(job.description) > 200 else job.description
            },
            "ranking": {
                "overall_score": ranking.overall_score,
                "percentile": calculate_percentile(ranking, db),
                "score_breakdown": {
                    "semantic_match": ranking.semantic_similarity_score,
                    "skills_match": ranking.skill_match_score,
                    "experience_match": ranking.experience_score,
                    "education_match": ranking.education_score
                },
                "matched_skills": ranking.matched_skills or [],
                "missing_skills": ranking.missing_skills or []
            }
        }

        logger.info(f"Candidate dashboard accessed for resume {resume.id}")

        return dashboard

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting candidate dashboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load dashboard: {str(e)}"
        )


@router.get("/feedback/{token}", response_model=Dict)
async def get_candidate_feedback(
    token: str,
    db: Session = Depends(get_db)
):
    """Get detailed feedback on resume quality and areas for improvement.

    Args:
        token: Candidate access token

    Returns:
        Comprehensive feedback with actionable recommendations
    """
    try:
        # Verify token
        resume = verify_candidate_token(token, db)
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid access token"
            )

        # Get resume quality analysis
        quality_report = quality_analyzer.analyze_resume_quality(
            resume.file_content or "",
            resume.parsed_data or {}
        )

        # Get ranking for additional insights
        ranking = db.query(Ranking).filter(
            Ranking.resume_id == resume.id
        ).first()

        feedback = {
            "resume_id": resume.id,
            "quality_analysis": quality_report,
            "strengths": generate_strengths(ranking, resume.parsed_data or {}),
            "areas_for_improvement": generate_improvement_areas(ranking, quality_report),
            "recommendations": generate_recommendations(ranking, quality_report)
        }

        logger.info(f"Feedback provided for resume {resume.id}")

        return feedback

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting candidate feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate feedback: {str(e)}"
        )


@router.get("/skill-gaps/{token}", response_model=Dict)
async def get_skill_gap_analysis(
    token: str,
    db: Session = Depends(get_db)
):
    """Get personalized skill gap analysis and learning paths.

    Args:
        token: Candidate access token

    Returns:
        Skill gaps with learning resources and roadmap
    """
    try:
        # Verify token
        resume = verify_candidate_token(token, db)
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid access token"
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

        # Analyze skill gaps
        gap_analysis = skill_gap_analyzer.analyze_individual_gap(
            candidate_skills,
            job_requirements
        )

        # Add personalized message
        gap_analysis["message"] = generate_skill_gap_message(gap_analysis)

        logger.info(f"Skill gap analysis provided for resume {resume.id}")

        return {
            "resume_id": resume.id,
            "job_title": job.title,
            "skill_gap_analysis": gap_analysis
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing skill gaps: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze skill gaps: {str(e)}"
        )


@router.get("/compare/{token}", response_model=Dict)
async def compare_with_pool(
    token: str,
    db: Session = Depends(get_db)
):
    """Compare candidate's profile with the applicant pool (anonymized).

    Args:
        token: Candidate access token

    Returns:
        Anonymous comparison statistics
    """
    try:
        # Verify token
        resume = verify_candidate_token(token, db)
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid access token"
            )

        # Get candidate's ranking
        candidate_ranking = db.query(Ranking).filter(
            Ranking.resume_id == resume.id
        ).first()

        if not candidate_ranking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ranking not found"
            )

        # Get all rankings for the same job
        all_rankings = db.query(Ranking).filter(
            Ranking.job_id == candidate_ranking.job_id
        ).all()

        if len(all_rankings) < 2:
            return {
                "message": "Not enough applicants for comparison yet",
                "total_applicants": len(all_rankings)
            }

        # Calculate statistics (anonymized)
        scores = [r.overall_score for r in all_rankings]
        candidate_score = candidate_ranking.overall_score

        comparison = {
            "your_score": candidate_score,
            "percentile": calculate_percentile(candidate_ranking, db),
            "pool_statistics": {
                "total_applicants": len(all_rankings),
                "average_score": round(sum(scores) / len(scores), 2),
                "highest_score": max(scores),
                "lowest_score": min(scores)
            },
            "score_distribution": {
                "excellent": len([s for s in scores if s >= 80]),
                "good": len([s for s in scores if 65 <= s < 80]),
                "moderate": len([s for s in scores if 50 <= s < 65]),
                "below_average": len([s for s in scores if s < 50])
            },
            "your_standing": get_standing_message(candidate_score, scores)
        }

        logger.info(f"Pool comparison provided for resume {resume.id}")

        return comparison

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing with pool: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare with pool: {str(e)}"
        )


@router.post("/request-feedback/{token}", response_model=Dict)
async def request_detailed_feedback(
    token: str,
    email: str = Query(..., description="Email to send detailed feedback to"),
    db: Session = Depends(get_db)
):
    """Request detailed feedback to be sent via email.

    Args:
        token: Candidate access token
        email: Email address to send feedback to

    Returns:
        Confirmation message
    """
    try:
        # Verify token
        resume = verify_candidate_token(token, db)
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid access token"
            )

        # In a real implementation, this would send an email
        # For now, we'll just log it
        logger.info(f"Detailed feedback requested for resume {resume.id} to email {email}")

        return {
            "message": "Detailed feedback request received",
            "status": "pending",
            "note": "You will receive an email with comprehensive feedback within 24 hours"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error requesting feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to request feedback: {str(e)}"
        )


# Helper functions

def calculate_percentile(ranking: Ranking, db: Session) -> float:
    """Calculate candidate's percentile in the pool."""
    all_rankings = db.query(Ranking).filter(
        Ranking.job_id == ranking.job_id
    ).all()

    if len(all_rankings) <= 1:
        return 100.0

    better_count = len([r for r in all_rankings if r.overall_score > ranking.overall_score])
    percentile = ((len(all_rankings) - better_count) / len(all_rankings)) * 100

    return round(percentile, 1)


def generate_strengths(ranking: Optional[Ranking], parsed_data: Dict) -> list:
    """Generate list of candidate strengths."""
    strengths = []

    if ranking:
        if ranking.overall_score >= 80:
            strengths.append("Excellent overall match for the position")

        if ranking.skill_match_score >= 80:
            strengths.append(f"Strong skill alignment ({len(ranking.matched_skills or [])} matching skills)")

        if ranking.experience_score >= 90:
            strengths.append("Relevant and substantial experience")

        if ranking.semantic_similarity_score >= 85:
            strengths.append("Resume closely aligns with job requirements")

    # Add strengths from parsed data
    if len(parsed_data.get("skills", [])) >= 10:
        strengths.append("Diverse skill set demonstrated")

    if parsed_data.get("total_experience_years", 0) >= 5:
        strengths.append("Experienced professional")

    return strengths if strengths else ["Application shows potential in several areas"]


def generate_improvement_areas(ranking: Optional[Ranking], quality_report: Dict) -> list:
    """Generate areas for improvement."""
    improvements = []

    if ranking:
        missing_skills = ranking.missing_skills or []
        if len(missing_skills) > 0:
            improvements.append(f"Consider acquiring skills: {', '.join(missing_skills[:3])}")

        if ranking.skill_match_score < 70:
            improvements.append("Strengthen alignment with required technical skills")

        if ranking.experience_score < 60:
            improvements.append("Highlight more relevant experience or projects")

    # Quality-based improvements
    if quality_report.get("overall_quality_tier") in ["Needs Improvement", "Average"]:
        improvements.append("Enhance resume formatting and structure")

    return improvements if improvements else ["Continue developing your professional profile"]


def generate_recommendations(ranking: Optional[Ranking], quality_report: Dict) -> list:
    """Generate actionable recommendations."""
    recommendations = []

    if quality_report.get("overall_score", 0) < 70:
        recommendations.extend(quality_report.get("suggestions", []))

    if ranking and len(ranking.missing_skills or []) > 0:
        recommendations.append("Focus on acquiring missing critical skills through online courses or projects")

    recommendations.append("Keep your resume updated with latest accomplishments and skills")
    recommendations.append("Tailor your resume to highlight experiences relevant to this role")

    return recommendations


def generate_skill_gap_message(gap_analysis: Dict) -> str:
    """Generate personalized skill gap message."""
    missing_count = gap_analysis["gaps"]["missing_required_count"]
    trainability_score = gap_analysis["trainability_assessment"]["score"]

    if missing_count == 0:
        return "Great! You have all the required skills for this position."
    elif trainability_score >= 75:
        return f"You're missing {missing_count} skills, but you have a strong foundation and can quickly acquire them."
    elif trainability_score >= 50:
        return f"You have {missing_count} skill gaps. With focused learning, you can become a strong fit for this role."
    else:
        return f"There are {missing_count} skill gaps. Consider a structured learning plan to meet the requirements."


def get_standing_message(candidate_score: float, all_scores: list) -> str:
    """Get standing message based on score."""
    avg_score = sum(all_scores) / len(all_scores) if all_scores else 0

    if candidate_score >= 80:
        return "Excellent - You're among the top candidates"
    elif candidate_score >= avg_score:
        return "Good - You're above average in the candidate pool"
    elif candidate_score >= 50:
        return "Moderate - You're in the middle range of candidates"
    else:
        return "Below average - Consider strengthening your application"
