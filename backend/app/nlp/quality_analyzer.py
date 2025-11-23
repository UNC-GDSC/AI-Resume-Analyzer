"""Resume quality scoring and analysis."""

import re
from typing import Dict, List
from collections import Counter
import numpy as np
from loguru import logger


class ResumeQualityAnalyzer:
    """Analyze resume quality and provide improvement suggestions."""

    def __init__(self):
        """Initialize quality analyzer."""
        self.action_verbs = {
            "achieved", "improved", "increased", "reduced", "managed", "led",
            "developed", "created", "implemented", "designed", "launched",
            "optimized", "streamlined", "coordinated", "initiated", "delivered"
        }

        self.weak_words = {
            "responsible for", "duties included", "worked on", "helped with",
            "assisted", "involved in", "participated"
        }

    def analyze_resume_quality(self, resume_text: str, parsed_data: Dict) -> Dict:
        """Comprehensive resume quality analysis.

        Args:
            resume_text: Raw resume text
            parsed_data: Parsed resume data

        Returns:
            Quality analysis with scores and suggestions
        """
        scores = {}
        suggestions = []
        strengths = []

        # 1. Length and completeness (0-100)
        length_score, length_feedback = self._analyze_length(resume_text)
        scores["length"] = length_score
        if length_score < 70:
            suggestions.extend(length_feedback)
        else:
            strengths.append("Resume has appropriate length")

        # 2. Action verb usage (0-100)
        action_score, action_feedback = self._analyze_action_verbs(resume_text)
        scores["action_verbs"] = action_score
        if action_score < 70:
            suggestions.extend(action_feedback)
        else:
            strengths.append("Strong use of action verbs")

        # 3. Quantifiable achievements (0-100)
        achievement_score, achievement_feedback = self._analyze_achievements(resume_text)
        scores["achievements"] = achievement_score
        if achievement_score < 60:
            suggestions.extend(achievement_feedback)
        else:
            strengths.append("Good quantifiable achievements")

        # 4. Contact information completeness (0-100)
        contact_score, contact_feedback = self._analyze_contact_info(parsed_data)
        scores["contact_info"] = contact_score
        if contact_score < 100:
            suggestions.extend(contact_feedback)
        else:
            strengths.append("Complete contact information")

        # 5. Structure and formatting (0-100)
        structure_score, structure_feedback = self._analyze_structure(resume_text)
        scores["structure"] = structure_score
        if structure_score < 70:
            suggestions.extend(structure_feedback)
        else:
            strengths.append("Well-structured resume")

        # 6. Keyword density (0-100)
        keyword_score, keyword_feedback = self._analyze_keywords(resume_text)
        scores["keywords"] = keyword_score
        if keyword_score < 60:
            suggestions.extend(keyword_feedback)
        else:
            strengths.append("Good keyword usage")

        # Calculate overall quality score
        weights = {
            "length": 0.15,
            "action_verbs": 0.20,
            "achievements": 0.25,
            "contact_info": 0.10,
            "structure": 0.15,
            "keywords": 0.15
        }

        overall_score = sum(scores[key] * weights[key] for key in scores)

        # Quality tier
        if overall_score >= 85:
            tier = "Excellent"
            tier_description = "This resume is well-crafted and highly competitive"
        elif overall_score >= 70:
            tier = "Good"
            tier_description = "This resume is solid with room for improvement"
        elif overall_score >= 55:
            tier = "Average"
            tier_description = "This resume needs significant improvements"
        else:
            tier = "Needs Improvement"
            tier_description = "This resume requires major revisions"

        return {
            "overall_score": round(overall_score, 2),
            "tier": tier,
            "tier_description": tier_description,
            "component_scores": scores,
            "strengths": strengths,
            "suggestions": suggestions,
            "metrics": {
                "word_count": len(resume_text.split()),
                "action_verb_count": self._count_action_verbs(resume_text),
                "quantifiable_achievements": self._count_numbers(resume_text),
                "weak_phrases": self._count_weak_phrases(resume_text)
            }
        }

    def _analyze_length(self, text: str) -> tuple:
        """Analyze resume length."""
        word_count = len(text.split())

        if 300 <= word_count <= 800:
            return 100, []
        elif 200 <= word_count < 300:
            return 75, ["Resume is a bit short. Consider adding more details about your experience."]
        elif 800 < word_count <= 1000:
            return 85, ["Resume is slightly long. Consider being more concise."]
        elif word_count > 1000:
            return 60, ["Resume is too long. Aim for 300-800 words for better readability."]
        else:
            return 40, ["Resume is too short. Add more details about your experience and skills."]

    def _analyze_action_verbs(self, text: str) -> tuple:
        """Analyze action verb usage."""
        text_lower = text.lower()
        action_count = sum(1 for verb in self.action_verbs if verb in text_lower)
        weak_count = sum(1 for phrase in self.weak_words if phrase in text_lower)

        if action_count >= 8 and weak_count <= 2:
            return 100, []
        elif action_count >= 5:
            feedback = []
            if weak_count > 2:
                feedback.append(f"Avoid weak phrases like 'responsible for' and 'helped with'. Use strong action verbs instead.")
            return 75, feedback
        else:
            return 50, ["Use more action verbs (achieved, improved, led, etc.) to describe your accomplishments."]

    def _analyze_achievements(self, text: str) -> tuple:
        """Analyze quantifiable achievements."""
        numbers = len(re.findall(r'\b\d+(?:\.\d+)?%?\b', text))
        percentages = len(re.findall(r'\b\d+(?:\.\d+)?%', text))

        if numbers >= 5 and percentages >= 2:
            return 100, []
        elif numbers >= 3:
            return 70, ["Add more quantifiable metrics (percentages, numbers, dollar amounts) to your achievements."]
        else:
            return 40, ["Quantify your achievements with specific numbers, percentages, or metrics."]

    def _analyze_contact_info(self, parsed_data: Dict) -> tuple:
        """Analyze contact information completeness."""
        score = 0
        feedback = []

        if parsed_data.get("email"):
            score += 50
        else:
            feedback.append("Add your email address")

        if parsed_data.get("phone"):
            score += 30
        else:
            feedback.append("Add your phone number")

        if parsed_data.get("name"):
            score += 20
        else:
            feedback.append("Ensure your name is clearly visible")

        return score, feedback

    def _analyze_structure(self, text: str) -> tuple:
        """Analyze resume structure."""
        score = 100
        feedback = []

        # Check for section headers
        common_sections = ["experience", "education", "skills", "summary"]
        text_lower = text.lower()
        found_sections = sum(1 for section in common_sections if section in text_lower)

        if found_sections < 2:
            score -= 30
            feedback.append("Include clear sections like Experience, Education, and Skills")

        # Check for bullet points or structured lists
        if not re.search(r'[•\-\*]', text) and text.count('\n') < 5:
            score -= 20
            feedback.append("Use bullet points to organize information")

        return max(score, 0), feedback

    def _analyze_keywords(self, text: str) -> tuple:
        """Analyze keyword usage."""
        text_lower = text.lower()

        # Industry keywords
        tech_keywords = ["software", "development", "programming", "data", "analysis",
                        "management", "project", "team", "leadership"]

        keyword_count = sum(1 for keyword in tech_keywords if keyword in text_lower)

        if keyword_count >= 5:
            return 100, []
        elif keyword_count >= 3:
            return 70, ["Include more industry-specific keywords relevant to your target role."]
        else:
            return 40, ["Add relevant industry keywords and technical terms to improve ATS compatibility."]

    def _count_action_verbs(self, text: str) -> int:
        """Count action verbs in text."""
        text_lower = text.lower()
        return sum(1 for verb in self.action_verbs if verb in text_lower)

    def _count_numbers(self, text: str) -> int:
        """Count numbers and percentages."""
        return len(re.findall(r'\b\d+(?:\.\d+)?%?\b', text))

    def _count_weak_phrases(self, text: str) -> int:
        """Count weak phrases."""
        text_lower = text.lower()
        return sum(1 for phrase in self.weak_words if phrase in text_lower)
