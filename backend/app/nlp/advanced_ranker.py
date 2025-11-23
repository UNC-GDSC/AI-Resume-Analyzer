"""Advanced ranking features with additional NLP techniques."""

import re
from typing import Dict, List
from collections import Counter
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from loguru import logger


class AdvancedRanker:
    """Advanced ranking features using TF-IDF and keyword extraction."""

    def __init__(self):
        """Initialize advanced ranker."""
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=100,
            stop_words='english',
            ngram_range=(1, 2)
        )

    def extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """Extract important keywords from text using TF-IDF.

        Args:
            text: Input text
            top_n: Number of top keywords to return

        Returns:
            List of keywords
        """
        try:
            # Fit and transform
            tfidf_matrix = self.tfidf_vectorizer.fit_transform([text])
            feature_names = self.tfidf_vectorizer.get_feature_names_out()

            # Get scores
            scores = tfidf_matrix.toarray()[0]

            # Get top keywords
            top_indices = scores.argsort()[-top_n:][::-1]
            keywords = [feature_names[i] for i in top_indices if scores[i] > 0]

            return keywords

        except Exception as e:
            logger.error(f"Keyword extraction failed: {str(e)}")
            return []

    def calculate_keyword_overlap(
        self, resume_text: str, job_text: str
    ) -> float:
        """Calculate keyword overlap between resume and job description.

        Args:
            resume_text: Resume text
            job_text: Job description text

        Returns:
            Overlap score (0-100)
        """
        resume_keywords = set(self.extract_keywords(resume_text, 20))
        job_keywords = set(self.extract_keywords(job_text, 20))

        if not job_keywords:
            return 0.0

        overlap = len(resume_keywords.intersection(job_keywords))
        score = (overlap / len(job_keywords)) * 100

        return min(score, 100.0)

    def analyze_experience_relevance(
        self, experience_list: List[Dict], job_keywords: List[str]
    ) -> float:
        """Analyze how relevant work experience is to job.

        Args:
            experience_list: List of experience entries
            job_keywords: Keywords from job description

        Returns:
            Relevance score (0-100)
        """
        if not experience_list or not job_keywords:
            return 50.0  # Neutral score

        # Combine all experience descriptions
        exp_text = " ".join([exp.get("description", "") for exp in experience_list])
        exp_text_lower = exp_text.lower()

        # Count keyword matches
        matches = sum(1 for keyword in job_keywords if keyword.lower() in exp_text_lower)

        if len(job_keywords) == 0:
            return 50.0

        score = (matches / len(job_keywords)) * 100
        return min(score, 100.0)

    def detect_leadership_indicators(self, text: str) -> Dict[str, any]:
        """Detect leadership experience indicators.

        Args:
            text: Resume text

        Returns:
            Dictionary with leadership indicators
        """
        leadership_keywords = [
            r"\bled\b", r"\bmanaged\b", r"\bdirected\b", r"\bsupervised\b",
            r"\bcoordinated\b", r"\bmentored\b", r"\bteam lead\b", r"\bmanager\b",
            r"\bdirector\b", r"\bhead of\b", r"\bvp\b", r"\bceo\b", r"\bcto\b"
        ]

        text_lower = text.lower()
        matches = []

        for pattern in leadership_keywords:
            if re.search(pattern, text_lower):
                matches.append(pattern.strip(r"\b"))

        return {
            "has_leadership": len(matches) > 0,
            "leadership_score": min((len(matches) / len(leadership_keywords)) * 100, 100),
            "indicators": matches
        }

    def calculate_cultural_fit_score(
        self, resume_text: str, company_values: List[str]
    ) -> float:
        """Calculate potential cultural fit based on language used.

        Args:
            resume_text: Resume text
            company_values: List of company values/keywords

        Returns:
            Cultural fit score (0-100)
        """
        if not company_values:
            return 50.0  # Neutral

        text_lower = resume_text.lower()
        matches = sum(1 for value in company_values if value.lower() in text_lower)

        score = (matches / len(company_values)) * 100
        return min(score, 100.0)

    def analyze_achievement_impact(self, text: str) -> Dict[str, any]:
        """Analyze achievements and quantifiable impact.

        Args:
            text: Resume text

        Returns:
            Achievement analysis
        """
        # Look for numbers and percentages (quantifiable achievements)
        numbers = re.findall(r'\b\d+(?:\.\d+)?%?\b', text)
        percentages = re.findall(r'\b\d+(?:\.\d+)?%', text)

        # Achievement verbs
        achievement_verbs = [
            r"\bachieved\b", r"\bimproved\b", r"\bincreased\b", r"\breduced\b",
            r"\bgenerated\b", r"\bsaved\b", r"\baccomplished\b", r"\bdelivered\b"
        ]

        text_lower = text.lower()
        achievement_count = sum(
            1 for verb in achievement_verbs if re.search(verb, text_lower)
        )

        return {
            "has_quantifiable_achievements": len(numbers) > 0,
            "number_count": len(numbers),
            "percentage_count": len(percentages),
            "achievement_verb_count": achievement_count,
            "impact_score": min(
                (achievement_count * 10 + len(percentages) * 5), 100
            )
        }
