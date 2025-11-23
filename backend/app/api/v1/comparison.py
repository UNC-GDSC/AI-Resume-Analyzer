"""Resume comparison API endpoints."""

from typing import List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from loguru import logger

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.job import Job
from app.models.ranking import Ranking
from app.models.resume import Resume

router = APIRouter()


@router.post("/compare", response_model=Dict)
async def compare_resumes(
    resume_ids: List[int] = Query(..., description="List of resume IDs to compare"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Compare multiple resumes side-by-side.

    Args:
        resume_ids: List of resume IDs to compare (2-5 resumes)
        current_user: Current authenticated user
        db: Database session

    Returns:
        Comprehensive comparison analysis
    """
    try:
        # Validate input
        if len(resume_ids) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least 2 resumes are required for comparison"
            )

        if len(resume_ids) > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 5 resumes can be compared at once"
            )

        user_id = int(current_user["sub"])

        # Get all resumes with their rankings
        comparisons = []
        job_id = None

        for resume_id in resume_ids:
            # Get resume (check ownership via job)
            resume = db.query(Resume).join(Job).filter(
                Resume.id == resume_id,
                Job.user_id == user_id
            ).first()

            if not resume:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Resume {resume_id} not found or access denied"
                )

            # Ensure all resumes are for the same job
            if job_id is None:
                job_id = resume.job_id
            elif job_id != resume.job_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="All resumes must be for the same job position"
                )

            # Get ranking
            ranking = db.query(Ranking).filter(
                Ranking.resume_id == resume_id,
                Ranking.job_id == job_id
            ).first()

            if not ranking:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Ranking not found for resume {resume_id}"
                )

            # Build comparison data
            parsed_data = resume.parsed_data or {}

            comparisons.append({
                "resume_id": resume_id,
                "filename": resume.filename,
                "candidate_name": resume.candidate_name or "Unknown",
                "scores": {
                    "overall": ranking.overall_score,
                    "semantic_similarity": ranking.semantic_similarity_score,
                    "skill_match": ranking.skill_match_score,
                    "experience": ranking.experience_score,
                    "education": ranking.education_score
                },
                "skills": {
                    "total_count": len(parsed_data.get("skills", [])),
                    "matched": ranking.matched_skills or [],
                    "missing": ranking.missing_skills or [],
                    "match_percentage": round(
                        (len(ranking.matched_skills or []) /
                         max(len(parsed_data.get("skills", [])), 1)) * 100,
                        1
                    )
                },
                "experience": {
                    "total_years": parsed_data.get("total_experience_years", 0),
                    "positions": len(parsed_data.get("experience", []))
                },
                "education": {
                    "degrees": len(parsed_data.get("education", [])),
                    "highest_degree": _get_highest_degree(parsed_data.get("education", []))
                },
                "contact": {
                    "email": parsed_data.get("email"),
                    "phone": parsed_data.get("phone")
                }
            })

        # Sort by overall score
        comparisons.sort(key=lambda x: x["scores"]["overall"], reverse=True)

        # Generate insights
        insights = _generate_comparison_insights(comparisons)

        # Get job info
        job = db.query(Job).filter(Job.id == job_id).first()

        logger.info(f"Compared {len(resume_ids)} resumes for job {job_id}")

        return {
            "job_id": job_id,
            "job_title": job.title if job else "Unknown",
            "total_candidates": len(comparisons),
            "candidates": comparisons,
            "comparison_matrix": _build_comparison_matrix(comparisons),
            "insights": insights,
            "winner": comparisons[0] if comparisons else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing resumes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare resumes: {str(e)}"
        )


@router.get("/top-candidates/{job_id}", response_model=Dict)
async def get_top_candidates_comparison(
    job_id: int,
    limit: int = Query(3, ge=2, le=10, description="Number of top candidates"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comparison of top candidates for a job.

    Args:
        job_id: Job ID
        limit: Number of top candidates to compare
        current_user: Current authenticated user
        db: Database session

    Returns:
        Comparison of top candidates
    """
    try:
        user_id = int(current_user["sub"])

        # Verify job ownership
        job = db.query(Job).filter(
            Job.id == job_id,
            Job.user_id == user_id
        ).first()

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )

        # Get top rankings
        top_rankings = (
            db.query(Ranking)
            .filter(Ranking.job_id == job_id)
            .order_by(Ranking.overall_score.desc())
            .limit(limit)
            .all()
        )

        if len(top_rankings) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not enough candidates to compare"
            )

        # Get resume IDs
        resume_ids = [r.resume_id for r in top_rankings]

        # Use the compare endpoint logic
        return await compare_resumes(resume_ids, current_user, db)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting top candidates comparison: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get top candidates comparison: {str(e)}"
        )


@router.post("/strengths-weaknesses", response_model=Dict)
async def compare_strengths_weaknesses(
    resume_ids: List[int] = Query(..., description="List of resume IDs"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Compare strengths and weaknesses of multiple candidates.

    Args:
        resume_ids: List of resume IDs to compare
        current_user: Current authenticated user
        db: Database session

    Returns:
        Strengths and weaknesses comparison
    """
    try:
        if len(resume_ids) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least 2 resumes are required"
            )

        user_id = int(current_user["sub"])

        comparisons = []

        for resume_id in resume_ids:
            # Get resume with ranking
            resume = db.query(Resume).join(Job).filter(
                Resume.id == resume_id,
                Job.user_id == user_id
            ).first()

            if not resume:
                continue

            ranking = db.query(Ranking).filter(
                Ranking.resume_id == resume_id
            ).first()

            if not ranking:
                continue

            # Analyze strengths and weaknesses
            strengths = []
            weaknesses = []

            # Score-based analysis
            if ranking.overall_score >= 80:
                strengths.append("Excellent overall match")
            elif ranking.overall_score < 50:
                weaknesses.append("Below average overall match")

            if ranking.skill_match_score >= 80:
                strengths.append(f"Strong skill match ({len(ranking.matched_skills or [])} skills)")
            elif ranking.skill_match_score < 60:
                weaknesses.append(f"Significant skill gaps ({len(ranking.missing_skills or [])} missing)")

            if ranking.experience_score >= 90:
                strengths.append("Exceptional experience level")
            elif ranking.experience_score < 60:
                weaknesses.append("Limited relevant experience")

            if ranking.education_score >= 85:
                strengths.append("Strong educational background")

            parsed_data = resume.parsed_data or {}

            if len(parsed_data.get("skills", [])) >= 15:
                strengths.append("Diverse skill set")

            if parsed_data.get("total_experience_years", 0) >= 10:
                strengths.append("Highly experienced professional")

            comparisons.append({
                "resume_id": resume_id,
                "filename": resume.filename,
                "overall_score": ranking.overall_score,
                "strengths": strengths,
                "weaknesses": weaknesses,
                "strength_count": len(strengths),
                "weakness_count": len(weaknesses)
            })

        # Sort by overall score
        comparisons.sort(key=lambda x: x["overall_score"], reverse=True)

        logger.info(f"Compared strengths/weaknesses for {len(resume_ids)} resumes")

        return {
            "total_compared": len(comparisons),
            "comparisons": comparisons,
            "summary": {
                "strongest_candidate": comparisons[0] if comparisons else None,
                "most_balanced": _find_most_balanced(comparisons)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing strengths/weaknesses: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare strengths/weaknesses: {str(e)}"
        )


# Helper functions

def _get_highest_degree(education_list: List[Dict]) -> str:
    """Get highest degree from education list."""
    if not education_list:
        return "None"

    degree_hierarchy = {
        "phd": 5,
        "doctorate": 5,
        "masters": 4,
        "master": 4,
        "mba": 4,
        "bachelor": 3,
        "associate": 2,
        "diploma": 1
    }

    highest = 0
    highest_degree = "None"

    for edu in education_list:
        degree = edu.get("degree", "").lower()
        for key, value in degree_hierarchy.items():
            if key in degree and value > highest:
                highest = value
                highest_degree = degree.capitalize()

    return highest_degree if highest_degree != "None" else education_list[0].get("degree", "Unknown")


def _build_comparison_matrix(comparisons: List[Dict]) -> Dict:
    """Build comparison matrix showing who wins in each category."""
    if not comparisons:
        return {}

    categories = ["overall", "semantic_similarity", "skill_match", "experience", "education"]

    matrix = {}

    for category in categories:
        best_score = max(c["scores"][category] for c in comparisons)
        winners = [
            c["filename"]
            for c in comparisons
            if c["scores"][category] == best_score
        ]

        matrix[category] = {
            "best_score": round(best_score, 2),
            "winners": winners
        }

    return matrix


def _generate_comparison_insights(comparisons: List[Dict]) -> List[str]:
    """Generate insights from comparison."""
    insights = []

    if len(comparisons) < 2:
        return insights

    # Score spread
    scores = [c["scores"]["overall"] for c in comparisons]
    score_spread = max(scores) - min(scores)

    if score_spread < 10:
        insights.append("Candidates are very evenly matched - consider cultural fit and soft skills")
    elif score_spread > 30:
        insights.append("Clear frontrunner emerged - significant gap between top and bottom candidates")

    # Top candidate analysis
    top = comparisons[0]
    if top["scores"]["overall"] >= 85:
        insights.append(f"Top candidate ({top['filename']}) is an excellent match for this position")

    if top["skills"]["match_percentage"] >= 90:
        insights.append(f"{top['filename']} has exceptional skill alignment")

    # Experience comparison
    avg_experience = sum(c["experience"]["total_years"] for c in comparisons) / len(comparisons)
    most_experienced = max(comparisons, key=lambda x: x["experience"]["total_years"])

    if most_experienced["experience"]["total_years"] > avg_experience * 1.5:
        insights.append(
            f"{most_experienced['filename']} has significantly more experience than others "
            f"({most_experienced['experience']['total_years']} years)"
        )

    # Skill gaps
    all_missing = set()
    for c in comparisons:
        all_missing.update(c["skills"]["missing"])

    common_gaps = []
    for skill in all_missing:
        count = sum(1 for c in comparisons if skill in c["skills"]["missing"])
        if count == len(comparisons):
            common_gaps.append(skill)

    if common_gaps:
        insights.append(
            f"All candidates lack: {', '.join(common_gaps[:3])}{'...' if len(common_gaps) > 3 else ''}"
        )

    return insights


def _find_most_balanced(comparisons: List[Dict]) -> Optional[Dict]:
    """Find candidate with most balanced profile (fewest weaknesses)."""
    if not comparisons:
        return None

    # Find candidate with best ratio of strengths to weaknesses
    best_ratio = -1
    most_balanced = None

    for c in comparisons:
        strengths = c["strength_count"]
        weaknesses = c["weakness_count"]

        # Calculate ratio (avoid division by zero)
        ratio = strengths / max(weaknesses, 1)

        if ratio > best_ratio:
            best_ratio = ratio
            most_balanced = c

    return most_balanced
