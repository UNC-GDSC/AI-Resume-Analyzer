"""Diversity and inclusion analysis."""

from typing import Dict, List
import re
from loguru import logger


class DiversityAnalyzer:
    """Analyze diversity metrics in candidate pool."""

    def __init__(self):
        """Initialize diversity analyzer."""
        # Note: This is a simplified version for demonstration
        # Real implementation would need more sophisticated NLP
        # and should be used carefully to avoid bias

        self.diversity_indicators = {
            "education_diversity": [
                "community college", "state university", "technical school",
                "online program", "bootcamp", "certification"
            ],
            "international_indicators": [
                "international", "visa", "foreign", "abroad", "overseas",
                "multilingual", "bilingual", "second language"
            ],
            "non_traditional_background": [
                "career change", "self-taught", "bootcamp", "non-traditional",
                "alternative education", "online learning"
            ]
        }

    def analyze_candidate_pool(
        self, resumes_data: List[Dict], job_data: Dict
    ) -> Dict:
        """Analyze diversity metrics across candidate pool.

        Args:
            resumes_data: List of parsed resume data
            job_data: Job description data

        Returns:
            Diversity analysis report
        """
        total_candidates = len(resumes_data)

        if total_candidates == 0:
            return self._empty_report()

        # Education diversity
        education_diversity = self._analyze_education_diversity(resumes_data)

        # International/multilingual candidates
        international_count = self._count_international_indicators(resumes_data)

        # Non-traditional backgrounds
        non_traditional_count = self._count_non_traditional(resumes_data)

        # Experience range diversity
        experience_diversity = self._analyze_experience_diversity(resumes_data)

        # Recommendations
        recommendations = self._generate_recommendations(
            total_candidates,
            education_diversity,
            international_count,
            non_traditional_count
        )

        return {
            "total_candidates": total_candidates,
            "education_diversity": {
                "score": education_diversity["score"],
                "institutions_count": education_diversity["unique_institutions"],
                "diversity_level": education_diversity["level"]
            },
            "international_representation": {
                "count": international_count,
                "percentage": (international_count / total_candidates) * 100
            },
            "non_traditional_backgrounds": {
                "count": non_traditional_count,
                "percentage": (non_traditional_count / total_candidates) * 100
            },
            "experience_diversity": experience_diversity,
            "diversity_score": self._calculate_overall_diversity_score(
                education_diversity["score"],
                international_count / total_candidates,
                non_traditional_count / total_candidates,
                experience_diversity["coefficient_of_variation"]
            ),
            "recommendations": recommendations,
            "insights": self._generate_insights(
                total_candidates,
                international_count,
                non_traditional_count,
                experience_diversity
            )
        }

    def _analyze_education_diversity(self, resumes_data: List[Dict]) -> Dict:
        """Analyze diversity of educational backgrounds."""
        institutions = set()
        education_levels = set()

        for resume in resumes_data:
            education = resume.get("education", [])
            for edu in education:
                institution = edu.get("institution")
                if institution:
                    institutions.add(institution.lower())

                degree = edu.get("degree", "").lower()
                if "phd" in degree or "doctorate" in degree:
                    education_levels.add("doctorate")
                elif "master" in degree or "mba" in degree:
                    education_levels.add("masters")
                elif "bachelor" in degree:
                    education_levels.add("bachelors")
                else:
                    education_levels.add("other")

        unique_count = len(institutions)
        total = len(resumes_data)

        # Calculate diversity score
        if total == 0:
            score = 0
        else:
            score = min((unique_count / total) * 100, 100)

        # Determine level
        if score >= 75:
            level = "High"
        elif score >= 50:
            level = "Moderate"
        else:
            level = "Low"

        return {
            "unique_institutions": unique_count,
            "education_levels": list(education_levels),
            "score": round(score, 2),
            "level": level
        }

    def _count_international_indicators(self, resumes_data: List[Dict]) -> int:
        """Count candidates with international indicators."""
        count = 0
        for resume in resumes_data:
            text = resume.get("raw_text", "").lower()
            for indicator in self.diversity_indicators["international_indicators"]:
                if indicator in text:
                    count += 1
                    break
        return count

    def _count_non_traditional(self, resumes_data: List[Dict]) -> int:
        """Count candidates with non-traditional backgrounds."""
        count = 0
        for resume in resumes_data:
            text = resume.get("raw_text", "").lower()
            for indicator in self.diversity_indicators["non_traditional_background"]:
                if indicator in text:
                    count += 1
                    break
        return count

    def _analyze_experience_diversity(self, resumes_data: List[Dict]) -> Dict:
        """Analyze diversity in experience levels."""
        experience_years = [
            resume.get("total_experience_years", 0)
            for resume in resumes_data
        ]

        if not experience_years:
            return {"min": 0, "max": 0, "avg": 0, "coefficient_of_variation": 0}

        import numpy as np

        exp_array = np.array(experience_years)
        mean_exp = np.mean(exp_array)
        std_exp = np.std(exp_array)

        # Coefficient of variation (measure of diversity)
        cv = (std_exp / mean_exp) if mean_exp > 0 else 0

        return {
            "min": float(np.min(exp_array)),
            "max": float(np.max(exp_array)),
            "avg": round(float(mean_exp), 2),
            "std_dev": round(float(std_exp), 2),
            "coefficient_of_variation": round(cv, 2),
            "diversity_level": "High" if cv > 0.5 else "Moderate" if cv > 0.3 else "Low"
        }

    def _calculate_overall_diversity_score(
        self, edu_score: float, intl_ratio: float, non_trad_ratio: float, exp_cv: float
    ) -> float:
        """Calculate overall diversity score."""
        # Weighted average
        score = (
            edu_score * 0.30 +
            (intl_ratio * 100) * 0.25 +
            (non_trad_ratio * 100) * 0.25 +
            min(exp_cv * 100, 100) * 0.20
        )
        return round(score, 2)

    def _generate_recommendations(
        self, total: int, edu_diversity: Dict, intl_count: int, non_trad_count: int
    ) -> List[str]:
        """Generate diversity recommendations."""
        recommendations = []

        if edu_diversity["score"] < 50:
            recommendations.append(
                "Consider expanding recruitment to include candidates from diverse educational institutions."
            )

        if intl_count / total < 0.10:
            recommendations.append(
                "Consider international candidates to increase global perspective diversity."
            )

        if non_trad_count / total < 0.15:
            recommendations.append(
                "Consider candidates with non-traditional backgrounds (bootcamps, career changers, self-taught)."
            )

        if total < 20:
            recommendations.append(
                "Expand candidate pool to get better diversity metrics and insights."
            )

        if not recommendations:
            recommendations.append(
                "Good diversity representation in the candidate pool. Continue current recruitment practices."
            )

        return recommendations

    def _generate_insights(
        self, total: int, intl_count: int, non_trad_count: int, exp_diversity: Dict
    ) -> List[str]:
        """Generate diversity insights."""
        insights = []

        intl_pct = (intl_count / total) * 100 if total > 0 else 0
        non_trad_pct = (non_trad_count / total) * 100 if total > 0 else 0

        if intl_pct > 20:
            insights.append(
                f"{intl_pct:.1f}% of candidates show international experience or multilingual capabilities."
            )

        if non_trad_pct > 25:
            insights.append(
                f"{non_trad_pct:.1f}% of candidates come from non-traditional backgrounds."
            )

        if exp_diversity["coefficient_of_variation"] > 0.5:
            insights.append(
                f"Wide range of experience levels ({exp_diversity['min']:.1f} to {exp_diversity['max']:.1f} years)."
            )

        return insights

    def _empty_report(self) -> Dict:
        """Return empty diversity report."""
        return {
            "total_candidates": 0,
            "education_diversity": {"score": 0, "institutions_count": 0, "diversity_level": "N/A"},
            "international_representation": {"count": 0, "percentage": 0},
            "non_traditional_backgrounds": {"count": 0, "percentage": 0},
            "experience_diversity": {"min": 0, "max": 0, "avg": 0, "coefficient_of_variation": 0},
            "diversity_score": 0,
            "recommendations": ["Not enough candidates to analyze diversity metrics."],
            "insights": []
        }
