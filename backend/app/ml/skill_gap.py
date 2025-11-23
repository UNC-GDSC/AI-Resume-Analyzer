"""Skill gap analysis and recommendations."""

from typing import Dict, List, Set
from collections import Counter
import numpy as np
from loguru import logger


class SkillGapAnalyzer:
    """Analyze skill gaps and provide recommendations."""

    def __init__(self):
        """Initialize skill gap analyzer."""
        self.skill_categories = self._load_skill_categories()
        self.learning_resources = self._load_learning_resources()

    def _load_skill_categories(self) -> Dict[str, List[str]]:
        """Load categorized skills."""
        return {
            "programming": ["python", "java", "javascript", "c++", "go", "rust"],
            "web": ["react", "angular", "vue", "node.js", "django", "flask"],
            "database": ["sql", "postgresql", "mongodb", "redis", "elasticsearch"],
            "cloud": ["aws", "azure", "gcp", "docker", "kubernetes"],
            "data_science": ["machine learning", "deep learning", "data analysis", "pandas", "numpy"],
            "devops": ["ci/cd", "jenkins", "gitlab", "terraform", "ansible"],
            "mobile": ["ios", "android", "react native", "flutter"],
            "testing": ["unit testing", "integration testing", "selenium", "pytest"]
        }

    def _load_learning_resources(self) -> Dict[str, Dict]:
        """Load learning resource recommendations."""
        return {
            "python": {
                "platforms": ["Coursera", "edX", "Python.org"],
                "difficulty": "Beginner to Advanced",
                "estimated_time": "3-6 months"
            },
            "react": {
                "platforms": ["React.dev", "Udemy", "Frontend Masters"],
                "difficulty": "Intermediate",
                "estimated_time": "2-4 months"
            },
            "aws": {
                "platforms": ["AWS Training", "A Cloud Guru", "Linux Academy"],
                "difficulty": "Intermediate to Advanced",
                "estimated_time": "3-6 months"
            },
            "machine learning": {
                "platforms": ["Coursera (Andrew Ng)", "Fast.ai", "Google ML Crash Course"],
                "difficulty": "Intermediate to Advanced",
                "estimated_time": "4-8 months"
            }
        }

    def analyze_candidate_pool_gaps(
        self, candidates_data: List[Dict], job_requirements: Dict
    ) -> Dict:
        """Analyze skill gaps across entire candidate pool.

        Args:
            candidates_data: List of candidate parsed data
            job_requirements: Job requirements with skills

        Returns:
            Comprehensive gap analysis
        """
        required_skills = set(s.lower() for s in job_requirements.get("required_skills", []))
        preferred_skills = set(s.lower() for s in job_requirements.get("preferred_skills", []))

        all_candidate_skills = []
        skill_coverage = {skill: 0 for skill in required_skills}

        # Collect all skills from candidates
        for candidate in candidates_data:
            candidate_skills = set(s.lower() for s in candidate.get("skills", []))
            all_candidate_skills.append(candidate_skills)

            # Track coverage of required skills
            for skill in required_skills:
                if skill in candidate_skills:
                    skill_coverage[skill] += 1

        total_candidates = len(candidates_data)

        # Calculate coverage percentages
        skill_coverage_pct = {
            skill: (count / total_candidates * 100) if total_candidates > 0 else 0
            for skill, count in skill_coverage.items()
        }

        # Identify critical gaps (skills with low coverage)
        critical_gaps = [
            skill for skill, pct in skill_coverage_pct.items()
            if pct < 30
        ]

        moderate_gaps = [
            skill for skill, pct in skill_coverage_pct.items()
            if 30 <= pct < 60
        ]

        # Find commonly available skills not in requirements
        all_skills_flat = [skill for skills in all_candidate_skills for skill in skills]
        skill_frequency = Counter(all_skills_flat)

        available_not_required = [
            (skill, count) for skill, count in skill_frequency.most_common(20)
            if skill not in required_skills and skill not in preferred_skills
        ]

        # Generate recommendations
        recommendations = self._generate_pool_recommendations(
            critical_gaps, moderate_gaps, total_candidates
        )

        return {
            "total_candidates_analyzed": total_candidates,
            "required_skills_count": len(required_skills),
            "skill_coverage": {
                "by_skill": skill_coverage_pct,
                "average_coverage": round(np.mean(list(skill_coverage_pct.values())), 2) if skill_coverage_pct else 0
            },
            "gaps": {
                "critical": critical_gaps,
                "moderate": moderate_gaps,
                "well_covered": [
                    skill for skill, pct in skill_coverage_pct.items()
                    if pct >= 60
                ]
            },
            "additional_skills_available": available_not_required[:10],
            "recommendations": recommendations,
            "sourcing_strategy": self._generate_sourcing_strategy(critical_gaps, moderate_gaps)
        }

    def analyze_individual_gap(
        self, candidate_skills: List[str], job_requirements: Dict
    ) -> Dict:
        """Analyze skill gaps for individual candidate.

        Args:
            candidate_skills: Candidate's skills
            job_requirements: Job requirements

        Returns:
            Individual gap analysis with learning paths
        """
        candidate_skills_set = set(s.lower() for s in candidate_skills)
        required_skills = set(s.lower() for s in job_requirements.get("required_skills", []))
        preferred_skills = set(s.lower() for s in job_requirements.get("preferred_skills", []))

        # Calculate gaps
        missing_required = required_skills - candidate_skills_set
        missing_preferred = preferred_skills - candidate_skills_set
        extra_skills = candidate_skills_set - required_skills - preferred_skills

        # Categorize missing skills
        categorized_gaps = self._categorize_skills(list(missing_required))

        # Generate learning paths
        learning_paths = self._generate_learning_paths(
            list(missing_required), list(missing_preferred)
        )

        # Calculate trainability score
        trainability_score = self._calculate_trainability_score(
            len(missing_required), len(required_skills), len(candidate_skills_set)
        )

        return {
            "gaps": {
                "missing_required": list(missing_required),
                "missing_preferred": list(missing_preferred),
                "missing_required_count": len(missing_required),
                "missing_preferred_count": len(missing_preferred)
            },
            "strengths": {
                "matched_required": list(required_skills & candidate_skills_set),
                "matched_preferred": list(preferred_skills & candidate_skills_set),
                "additional_relevant": list(extra_skills)[:10]
            },
            "categorized_gaps": categorized_gaps,
            "learning_paths": learning_paths,
            "trainability_assessment": {
                "score": trainability_score,
                "level": self._get_trainability_level(trainability_score),
                "recommendation": self._get_training_recommendation(trainability_score)
            },
            "priority_skills_to_acquire": self._prioritize_skills(
                list(missing_required), job_requirements
            )
        }

    def _categorize_skills(self, skills: List[str]) -> Dict[str, List[str]]:
        """Categorize skills by type."""
        categorized = {}
        uncategorized = []

        for skill in skills:
            found = False
            for category, category_skills in self.skill_categories.items():
                if skill in category_skills:
                    if category not in categorized:
                        categorized[category] = []
                    categorized[category].append(skill)
                    found = True
                    break

            if not found:
                uncategorized.append(skill)

        if uncategorized:
            categorized["other"] = uncategorized

        return categorized

    def _generate_learning_paths(
        self, required_gaps: List[str], preferred_gaps: List[str]
    ) -> List[Dict]:
        """Generate learning paths for skill gaps."""
        paths = []

        # Priority 1: Required skills
        for skill in required_gaps[:5]:  # Top 5 required
            resource_info = self.learning_resources.get(
                skill,
                {
                    "platforms": ["Online courses", "Documentation", "Practice projects"],
                    "difficulty": "Varies",
                    "estimated_time": "2-4 months"
                }
            )

            paths.append({
                "skill": skill,
                "priority": "High",
                "type": "Required",
                "learning_resources": resource_info["platforms"],
                "difficulty": resource_info["difficulty"],
                "estimated_time": resource_info["estimated_time"],
                "suggested_order": len(paths) + 1
            })

        # Priority 2: Preferred skills (top 3)
        for skill in preferred_gaps[:3]:
            resource_info = self.learning_resources.get(
                skill,
                {
                    "platforms": ["Online courses", "Documentation"],
                    "difficulty": "Varies",
                    "estimated_time": "1-3 months"
                }
            )

            paths.append({
                "skill": skill,
                "priority": "Medium",
                "type": "Preferred",
                "learning_resources": resource_info["platforms"],
                "difficulty": resource_info["difficulty"],
                "estimated_time": resource_info["estimated_time"],
                "suggested_order": len(paths) + 1
            })

        return paths

    def _calculate_trainability_score(
        self, missing_count: int, total_required: int, current_skills: int
    ) -> float:
        """Calculate how trainable a candidate is."""
        if total_required == 0:
            return 100.0

        # Base score from skill match
        match_rate = (total_required - missing_count) / total_required
        base_score = match_rate * 70  # Up to 70 points

        # Bonus for having many skills (shows learning ability)
        learning_bonus = min(current_skills / 10 * 30, 30)  # Up to 30 points

        # Penalty for too many gaps
        gap_penalty = min(missing_count * 5, 30)

        score = base_score + learning_bonus - gap_penalty
        return max(min(score, 100), 0)

    def _get_trainability_level(self, score: float) -> str:
        """Get trainability level from score."""
        if score >= 75:
            return "Highly Trainable"
        elif score >= 50:
            return "Trainable"
        elif score >= 25:
            return "Moderately Trainable"
        else:
            return "Significant Training Required"

    def _get_training_recommendation(self, score: float) -> str:
        """Get training recommendation."""
        if score >= 75:
            return "Candidate can quickly acquire missing skills with minimal training"
        elif score >= 50:
            return "Candidate shows good potential with structured training program"
        elif score >= 25:
            return "Consider if willing to invest in extended training period"
        else:
            return "Extensive training required; consider candidates with better skill match"

    def _prioritize_skills(self, missing_skills: List[str], job_requirements: Dict) -> List[Dict]:
        """Prioritize which skills to acquire first."""
        prioritized = []

        # Simple priority based on skill category
        for skill in missing_skills[:10]:  # Top 10
            category = "other"
            for cat, skills in self.skill_categories.items():
                if skill in skills:
                    category = cat
                    break

            # Higher priority for programming and core skills
            priority_score = 3 if category in ["programming", "database"] else 2

            prioritized.append({
                "skill": skill,
                "priority_score": priority_score,
                "category": category,
                "urgency": "High" if priority_score == 3 else "Medium"
            })

        # Sort by priority score
        prioritized.sort(key=lambda x: x["priority_score"], reverse=True)

        return prioritized

    def _generate_pool_recommendations(
        self, critical_gaps: List[str], moderate_gaps: List[str], total_candidates: int
    ) -> List[str]:
        """Generate recommendations for hiring manager."""
        recommendations = []

        if critical_gaps:
            recommendations.append(
                f"Critical skill gaps identified in {len(critical_gaps)} areas: {', '.join(critical_gaps[:3])}. "
                "Consider expanding recruitment to these skill sets."
            )

        if total_candidates < 20:
            recommendations.append(
                "Small candidate pool. Recommend continuing recruitment for 1-2 more weeks."
            )

        if moderate_gaps:
            recommendations.append(
                f"Moderate gaps in {len(moderate_gaps)} skills. Consider candidates with transferable skills "
                "and willingness to learn."
            )

        if not critical_gaps and total_candidates >= 20:
            recommendations.append(
                "Strong candidate pool with good skill coverage. Proceed with interviews."
            )

        return recommendations

    def _generate_sourcing_strategy(
        self, critical_gaps: List[str], moderate_gaps: List[str]
    ) -> Dict:
        """Generate targeted sourcing strategy."""
        strategy = {
            "target_skills": critical_gaps + moderate_gaps[:3],
            "recommended_channels": [],
            "search_keywords": [],
            "alternative_titles": []
        }

        # Recommend channels based on gaps
        if any(skill in ["python", "java", "javascript"] for skill in critical_gaps):
            strategy["recommended_channels"].append("GitHub")
            strategy["recommended_channels"].append("Stack Overflow")

        if any(skill in ["aws", "azure", "kubernetes"] for skill in critical_gaps):
            strategy["recommended_channels"].append("AWS/Azure communities")
            strategy["recommended_channels"].append("DevOps forums")

        # Generate search keywords
        strategy["search_keywords"] = critical_gaps[:5]

        return strategy
