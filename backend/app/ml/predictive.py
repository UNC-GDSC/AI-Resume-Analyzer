"""Predictive analytics using machine learning models."""

import numpy as np
from typing import Dict, List, Optional
import pickle
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from loguru import logger


class PredictiveAnalyzer:
    """Predict hiring outcomes using machine learning."""

    def __init__(self):
        """Initialize predictive analyzer."""
        self.models_dir = Path("models")
        self.models_dir.mkdir(exist_ok=True)

        # Initialize models
        self.success_classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.time_to_hire_regressor = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=5,
            random_state=42
        )
        self.scaler = StandardScaler()

        # Load pre-trained models if available
        self._load_models()

    def predict_hiring_success(self, ranking_features: Dict) -> Dict:
        """Predict likelihood of successful hire.

        Args:
            ranking_features: Features from ranking analysis

        Returns:
            Prediction with confidence score
        """
        # Extract features
        features = self._extract_features(ranking_features)

        # For demonstration, use rule-based prediction
        # In production, this would use trained ML model
        overall_score = ranking_features.get("overall_score", 0)
        skill_match = ranking_features.get("skill_match_score", 0)
        experience_score = ranking_features.get("experience_score", 0)

        # Calculate success probability
        if overall_score >= 85 and skill_match >= 80:
            success_probability = 0.85
            tier = "Very High"
        elif overall_score >= 70 and skill_match >= 70:
            success_probability = 0.70
            tier = "High"
        elif overall_score >= 55:
            success_probability = 0.50
            tier = "Moderate"
        else:
            success_probability = 0.30
            tier = "Low"

        # Generate insights
        insights = self._generate_success_insights(
            overall_score, skill_match, experience_score
        )

        return {
            "success_probability": round(success_probability, 3),
            "confidence_tier": tier,
            "predicted_performance": self._predict_performance_level(overall_score),
            "risk_factors": self._identify_risk_factors(ranking_features),
            "success_factors": self._identify_success_factors(ranking_features),
            "insights": insights,
            "recommendation": self._generate_hiring_recommendation(success_probability)
        }

    def predict_time_to_hire(self, job_features: Dict, market_data: Dict = None) -> Dict:
        """Predict time to hire for a position.

        Args:
            job_features: Job characteristics
            market_data: Market conditions (optional)

        Returns:
            Time to hire prediction
        """
        # Base time by job level
        job_level_days = {
            "entry": 30,
            "mid": 45,
            "senior": 60,
            "executive": 90
        }

        # Determine job level from requirements
        required_years = job_features.get("experience_years", 3)
        if required_years <= 2:
            level = "entry"
        elif required_years <= 5:
            level = "mid"
        elif required_years <= 10:
            level = "senior"
        else:
            level = "executive"

        base_days = job_level_days[level]

        # Adjust based on skill requirements
        required_skills = job_features.get("required_skills", [])
        skill_complexity_factor = min(len(required_skills) / 10, 1.5)

        # Calculate final prediction
        predicted_days = int(base_days * skill_complexity_factor)

        return {
            "predicted_days": predicted_days,
            "predicted_weeks": round(predicted_days / 7, 1),
            "job_level": level,
            "confidence_range": {
                "min_days": int(predicted_days * 0.8),
                "max_days": int(predicted_days * 1.3)
            },
            "factors": {
                "job_level_impact": level,
                "skill_complexity": round(skill_complexity_factor, 2),
                "required_skills_count": len(required_skills)
            },
            "recommendations": self._generate_time_to_hire_recommendations(predicted_days)
        }

    def analyze_candidate_pool_quality(
        self, rankings: List[Dict], job_requirements: Dict
    ) -> Dict:
        """Analyze overall quality of candidate pool.

        Args:
            rankings: List of candidate rankings
            job_requirements: Job requirements

        Returns:
            Pool quality analysis
        """
        if not rankings:
            return self._empty_pool_analysis()

        scores = [r["overall_score"] for r in rankings]

        # Calculate statistics
        avg_score = np.mean(scores)
        median_score = np.median(scores)
        std_score = np.std(scores)

        # Quality tier
        if avg_score >= 75:
            quality_tier = "Excellent"
            quality_desc = "Outstanding candidate pool with multiple strong candidates"
        elif avg_score >= 60:
            quality_tier = "Good"
            quality_desc = "Solid candidate pool with several qualified candidates"
        elif avg_score >= 45:
            quality_tier = "Fair"
            quality_desc = "Adequate pool but may need to expand search"
        else:
            quality_tier = "Poor"
            quality_desc = "Weak candidate pool, recommend expanding recruitment efforts"

        # Count candidates by tier
        excellent = sum(1 for s in scores if s >= 80)
        good = sum(1 for s in scores if 65 <= s < 80)
        moderate = sum(1 for s in scores if 50 <= s < 65)
        poor = sum(1 for s in scores if s < 50)

        # Predict hiring success rate
        hiring_success_rate = self._predict_pool_success_rate(avg_score, len(rankings))

        return {
            "total_candidates": len(rankings),
            "quality_tier": quality_tier,
            "quality_description": quality_desc,
            "statistics": {
                "average_score": round(avg_score, 2),
                "median_score": round(median_score, 2),
                "std_deviation": round(std_score, 2),
                "top_score": round(max(scores), 2),
                "lowest_score": round(min(scores), 2)
            },
            "distribution": {
                "excellent": {"count": excellent, "percentage": round(excellent/len(rankings)*100, 1)},
                "good": {"count": good, "percentage": round(good/len(rankings)*100, 1)},
                "moderate": {"count": moderate, "percentage": round(moderate/len(rankings)*100, 1)},
                "poor": {"count": poor, "percentage": round(poor/len(rankings)*100, 1)}
            },
            "predicted_hiring_success_rate": round(hiring_success_rate, 2),
            "recommendations": self._generate_pool_recommendations(
                quality_tier, len(rankings), avg_score
            ),
            "action_items": self._generate_action_items(quality_tier, excellent, len(rankings))
        }

    def _extract_features(self, ranking_features: Dict) -> np.ndarray:
        """Extract features for ML model."""
        features = [
            ranking_features.get("overall_score", 0),
            ranking_features.get("semantic_similarity_score", 0),
            ranking_features.get("skill_match_score", 0),
            ranking_features.get("experience_score", 0),
            ranking_features.get("education_score", 0),
            len(ranking_features.get("matched_skills", [])),
            len(ranking_features.get("missing_skills", []))
        ]
        return np.array(features).reshape(1, -1)

    def _predict_performance_level(self, overall_score: float) -> str:
        """Predict employee performance level."""
        if overall_score >= 85:
            return "High Performer"
        elif overall_score >= 70:
            return "Solid Performer"
        elif overall_score >= 55:
            return "Average Performer"
        else:
            return "Below Average"

    def _identify_risk_factors(self, features: Dict) -> List[str]:
        """Identify hiring risk factors."""
        risks = []

        if features.get("overall_score", 0) < 60:
            risks.append("Overall score below recommended threshold")

        if features.get("skill_match_score", 0) < 70:
            risks.append("Significant skill gaps identified")

        missing_skills = features.get("missing_skills", [])
        if len(missing_skills) > 3:
            risks.append(f"Missing {len(missing_skills)} required skills")

        if features.get("experience_score", 0) < 60:
            risks.append("Experience level below requirements")

        return risks if risks else ["No significant risk factors identified"]

    def _identify_success_factors(self, features: Dict) -> List[str]:
        """Identify factors indicating success."""
        factors = []

        if features.get("overall_score", 0) >= 80:
            factors.append("Excellent overall match for the role")

        if features.get("semantic_similarity_score", 0) >= 85:
            factors.append("Strong alignment with job description")

        matched_skills = features.get("matched_skills", [])
        if len(matched_skills) >= 5:
            factors.append(f"Strong skill match ({len(matched_skills)} skills)")

        if features.get("experience_score", 0) >= 90:
            factors.append("Exceptional experience level")

        return factors if factors else ["Candidate shows potential in several areas"]

    def _generate_success_insights(
        self, overall_score: float, skill_match: float, experience: float
    ) -> List[str]:
        """Generate insights about hiring success."""
        insights = []

        if overall_score >= 80 and skill_match >= 75:
            insights.append(
                "This candidate has a high probability of success based on strong "
                "skill alignment and overall qualifications."
            )

        if experience >= 100:
            insights.append(
                "Candidate's experience exceeds requirements, indicating potential "
                "for immediate impact and possible leadership opportunities."
            )

        if skill_match < 70:
            insights.append(
                "While showing potential, candidate would benefit from training in "
                "key areas to fully meet role requirements."
            )

        return insights

    def _generate_hiring_recommendation(self, probability: float) -> str:
        """Generate hiring recommendation."""
        if probability >= 0.75:
            return "Strong Hire - Recommend moving forward immediately"
        elif probability >= 0.60:
            return "Hire - Solid candidate worth interviewing"
        elif probability >= 0.45:
            return "Maybe - Consider if stronger candidates unavailable"
        else:
            return "No Hire - Look for better-qualified candidates"

    def _predict_pool_success_rate(self, avg_score: float, pool_size: int) -> float:
        """Predict hiring success rate from pool."""
        base_rate = min(avg_score / 100, 0.9)
        size_factor = min(pool_size / 50, 1.2)  # More candidates = higher success
        return min(base_rate * size_factor * 100, 95)

    def _generate_pool_recommendations(
        self, quality: str, count: int, avg_score: float
    ) -> List[str]:
        """Generate recommendations for candidate pool."""
        recommendations = []

        if quality == "Poor":
            recommendations.append("Expand recruitment channels immediately")
            recommendations.append("Consider relaxing non-essential requirements")
            recommendations.append("Increase employer branding efforts")
        elif quality == "Fair":
            recommendations.append("Continue recruiting to increase pool size")
            recommendations.append("Focus on passive candidate outreach")
        elif count < 10:
            recommendations.append("Aim for at least 15-20 qualified candidates")
        else:
            recommendations.append("Strong candidate pool - proceed to interviews")

        return recommendations

    def _generate_action_items(
        self, quality: str, excellent_count: int, total: int
    ) -> List[str]:
        """Generate action items based on pool quality."""
        actions = []

        if excellent_count >= 3:
            actions.append("Schedule interviews with top 3-5 candidates immediately")

        if quality in ["Poor", "Fair"]:
            actions.append("Review and optimize job posting for better attraction")
            actions.append("Consider salary/benefits competitiveness")

        if total < 20:
            actions.append("Continue active recruitment for 1-2 more weeks")

        return actions

    def _generate_time_to_hire_recommendations(self, predicted_days: int) -> List[str]:
        """Generate recommendations to optimize hiring timeline."""
        recommendations = []

        if predicted_days > 60:
            recommendations.append("Consider streamlining interview process")
            recommendations.append("Prepare decision-makers for timely evaluation")

        recommendations.append("Schedule interviews within first week of qualified applications")
        recommendations.append("Prepare offer package in advance to move quickly on top candidates")

        return recommendations

    def _empty_pool_analysis(self) -> Dict:
        """Return empty pool analysis."""
        return {
            "total_candidates": 0,
            "quality_tier": "N/A",
            "quality_description": "No candidates in pool",
            "recommendations": ["Begin recruitment immediately"]
        }

    def _load_models(self):
        """Load pre-trained models if available."""
        try:
            success_model_path = self.models_dir / "success_classifier.pkl"
            if success_model_path.exists():
                with open(success_model_path, "rb") as f:
                    self.success_classifier = pickle.load(f)
                logger.info("Loaded pre-trained success classifier")
        except Exception as e:
            logger.warning(f"Could not load models: {str(e)}")

    def save_models(self):
        """Save trained models."""
        try:
            with open(self.models_dir / "success_classifier.pkl", "wb") as f:
                pickle.dump(self.success_classifier, f)
            logger.info("Saved ML models")
        except Exception as e:
            logger.error(f"Error saving models: {str(e)}")
