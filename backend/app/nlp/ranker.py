"""Resume ranking algorithm using NLP and ML."""

import numpy as np
from typing import Dict, List, Tuple
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from loguru import logger


class ResumeRanker:
    """Rank resumes against job descriptions using multiple NLP techniques."""

    def __init__(self):
        """Initialize ranker with sentence transformer model."""
        try:
            self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
            logger.info("Sentence transformer model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading sentence transformer: {str(e)}")
            raise

    def compute_embedding(self, text: str) -> List[float]:
        """Compute semantic embedding for text.

        Args:
            text: Input text

        Returns:
            Embedding vector as list
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def compute_semantic_similarity(
        self, resume_embedding: List[float], job_embedding: List[float]
    ) -> float:
        """Compute semantic similarity between resume and job.

        Args:
            resume_embedding: Resume text embedding
            job_embedding: Job description embedding

        Returns:
            Similarity score (0-100)
        """
        resume_vec = np.array(resume_embedding).reshape(1, -1)
        job_vec = np.array(job_embedding).reshape(1, -1)

        similarity = cosine_similarity(resume_vec, job_vec)[0][0]

        # Convert from [-1, 1] to [0, 100]
        score = ((similarity + 1) / 2) * 100

        return float(score)

    def compute_skill_match_score(
        self, resume_skills: List[str], required_skills: List[str], preferred_skills: List[str] = None
    ) -> Tuple[float, Dict]:
        """Compute skill matching score.

        Args:
            resume_skills: Skills from resume
            required_skills: Required skills from job
            preferred_skills: Preferred skills from job

        Returns:
            Tuple of (score, details_dict)
        """
        if preferred_skills is None:
            preferred_skills = []

        resume_skills_set = set(skill.lower() for skill in resume_skills)
        required_skills_set = set(skill.lower() for skill in required_skills)
        preferred_skills_set = set(skill.lower() for skill in preferred_skills)

        # Find matched skills
        matched_required = resume_skills_set.intersection(required_skills_set)
        matched_preferred = resume_skills_set.intersection(preferred_skills_set)
        missing_required = required_skills_set - resume_skills_set

        # Calculate score
        # Required skills: 70% weight, Preferred skills: 30% weight
        if required_skills_set:
            required_score = (len(matched_required) / len(required_skills_set)) * 70
        else:
            required_score = 70  # If no required skills specified, give full points

        if preferred_skills_set:
            preferred_score = (len(matched_preferred) / len(preferred_skills_set)) * 30
        else:
            preferred_score = 30  # If no preferred skills specified, give full points

        total_score = required_score + preferred_score

        details = {
            "matched_skills": sorted(list(matched_required.union(matched_preferred))),
            "missing_skills": sorted(list(missing_required)),
            "match_percentage": {
                "required": round((len(matched_required) / len(required_skills_set) * 100) if required_skills_set else 100, 2),
                "preferred": round((len(matched_preferred) / len(preferred_skills_set) * 100) if preferred_skills_set else 100, 2),
            },
        }

        return float(total_score), details

    def compute_experience_score(
        self, resume_years: float, required_years: int = None
    ) -> float:
        """Compute experience matching score.

        Args:
            resume_years: Years of experience from resume
            required_years: Required years from job description

        Returns:
            Experience score (0-100)
        """
        if required_years is None:
            # If no requirement specified, give score based on experience level
            if resume_years >= 10:
                return 100.0
            elif resume_years >= 5:
                return 85.0
            elif resume_years >= 3:
                return 70.0
            elif resume_years >= 1:
                return 55.0
            else:
                return 40.0

        # Score based on how well experience matches requirement
        if resume_years >= required_years:
            # Give full score if meets requirement
            # Bonus for significantly more experience (up to 20% bonus)
            bonus = min((resume_years - required_years) / required_years * 20, 20)
            return min(100.0 + bonus, 120.0)  # Cap at 120 for exceptional candidates
        else:
            # Penalize proportionally for less experience
            score = (resume_years / required_years) * 100
            return max(float(score), 20.0)  # Minimum 20 points

    def compute_education_score(
        self, resume_education: List[Dict], required_education: str = None
    ) -> float:
        """Compute education matching score.

        Args:
            resume_education: Education from resume
            required_education: Required education level

        Returns:
            Education score (0-100)
        """
        if not resume_education:
            return 40.0  # Base score if no education info

        education_hierarchy = {
            "phd": 5,
            "master": 4,
            "bachelor": 3,
            "associate": 2,
            "high school": 1,
        }

        # Find highest degree in resume
        resume_max_level = 0
        for edu in resume_education:
            degree = edu.get("degree", "").lower()
            for level, rank in education_hierarchy.items():
                if level in degree:
                    resume_max_level = max(resume_max_level, rank)

        if required_education is None:
            # No specific requirement - score based on level
            level_scores = {5: 100, 4: 90, 3: 80, 2: 70, 1: 60}
            return float(level_scores.get(resume_max_level, 50))

        # Compare with requirement
        required_level = education_hierarchy.get(required_education.lower(), 3)

        if resume_max_level >= required_level:
            # Meets or exceeds requirement
            return 100.0
        elif resume_max_level == required_level - 1:
            # One level below
            return 70.0
        else:
            # More than one level below
            return 50.0

    def rank_resume(
        self,
        resume_data: Dict,
        job_data: Dict,
        resume_embedding: List[float],
        job_embedding: List[float],
    ) -> Dict:
        """Rank a single resume against a job description.

        Args:
            resume_data: Parsed resume data
            job_data: Parsed job data
            resume_embedding: Resume text embedding
            job_embedding: Job description embedding

        Returns:
            Dictionary containing ranking results
        """
        # 1. Semantic Similarity (40% weight)
        semantic_score = self.compute_semantic_similarity(resume_embedding, job_embedding)

        # 2. Skill Matching (30% weight)
        skill_score, skill_details = self.compute_skill_match_score(
            resume_data.get("skills", []),
            job_data.get("required_skills", []),
            job_data.get("preferred_skills", []),
        )

        # 3. Experience (20% weight)
        experience_score = self.compute_experience_score(
            resume_data.get("total_experience_years", 0),
            job_data.get("experience_years"),
        )

        # 4. Education (10% weight)
        education_score = self.compute_education_score(
            resume_data.get("education", []),
            job_data.get("education_level"),
        )

        # Calculate weighted overall score
        overall_score = (
            semantic_score * 0.40 +
            skill_score * 0.30 +
            min(experience_score, 100) * 0.20 +  # Cap experience at 100 for overall calc
            education_score * 0.10
        )

        # Generate strengths and weaknesses
        strengths = []
        weaknesses = []

        if semantic_score >= 75:
            strengths.append("Strong semantic match with job description")
        elif semantic_score < 50:
            weaknesses.append("Resume content doesn't align well with job description")

        if skill_score >= 70:
            strengths.append(f"Good skill match ({len(skill_details['matched_skills'])} matching skills)")
        elif skill_details['missing_skills']:
            weaknesses.append(f"Missing {len(skill_details['missing_skills'])} required skills")

        if experience_score >= 100:
            strengths.append("Exceptional experience level for this role")
        elif experience_score >= 80:
            strengths.append("Good experience level")
        elif experience_score < 60:
            weaknesses.append("Below required experience level")

        if education_score >= 90:
            strengths.append("Strong educational background")
        elif education_score < 60:
            weaknesses.append("Education level below preferred requirement")

        # Generate summary
        if overall_score >= 80:
            summary = "Excellent match for this position. Highly recommended candidate."
        elif overall_score >= 65:
            summary = "Good match for this position. Recommended for interview."
        elif overall_score >= 50:
            summary = "Moderate match. May be suitable with additional screening."
        else:
            summary = "Below threshold match. Consider other candidates first."

        return {
            "overall_score": round(overall_score, 2),
            "semantic_similarity_score": round(semantic_score, 2),
            "skill_match_score": round(skill_score, 2),
            "experience_score": round(min(experience_score, 100), 2),
            "education_score": round(education_score, 2),
            "matched_skills": skill_details["matched_skills"],
            "missing_skills": skill_details["missing_skills"],
            "summary": summary,
            "strengths": strengths,
            "weaknesses": weaknesses,
        }
