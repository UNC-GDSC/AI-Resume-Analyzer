"""Export service for generating reports."""

import csv
import io
from typing import List
from datetime import datetime
from app.models.ranking import Ranking


class ExportService:
    """Service for exporting data to various formats."""

    @staticmethod
    def export_rankings_to_csv(rankings: List[Ranking], job_title: str) -> str:
        """Export rankings to CSV format.

        Args:
            rankings: List of rankings
            job_title: Job title for the report

        Returns:
            CSV string
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            "Rank",
            "Candidate Name",
            "Email",
            "Filename",
            "Overall Score",
            "Semantic Score",
            "Skill Match Score",
            "Experience Score",
            "Education Score",
            "Matched Skills",
            "Missing Skills",
            "Summary",
            "Date Analyzed"
        ])

        # Write data
        for ranking in rankings:
            writer.writerow([
                ranking.rank_position or "",
                ranking.resume.candidate_name or "Unknown",
                ranking.resume.email or "",
                ranking.resume.filename,
                f"{ranking.overall_score:.2f}",
                f"{ranking.semantic_similarity_score:.2f}",
                f"{ranking.skill_match_score:.2f}",
                f"{ranking.experience_score:.2f}",
                f"{ranking.education_score:.2f}",
                ", ".join(ranking.matched_skills or []),
                ", ".join(ranking.missing_skills or []),
                ranking.summary or "",
                ranking.created_at.strftime("%Y-%m-%d %H:%M")
            ])

        return output.getvalue()

    @staticmethod
    def generate_analytics_report(rankings: List[Ranking]) -> dict:
        """Generate analytics report from rankings.

        Args:
            rankings: List of rankings

        Returns:
            Analytics dictionary
        """
        if not rankings:
            return {
                "total_candidates": 0,
                "average_score": 0,
                "score_distribution": {},
                "top_skills": [],
                "common_missing_skills": []
            }

        total = len(rankings)
        avg_score = sum(r.overall_score for r in rankings) / total

        # Score distribution
        score_ranges = {
            "80-100": 0,
            "65-79": 0,
            "50-64": 0,
            "0-49": 0
        }

        all_matched_skills = []
        all_missing_skills = []

        for ranking in rankings:
            score = ranking.overall_score
            if score >= 80:
                score_ranges["80-100"] += 1
            elif score >= 65:
                score_ranges["65-79"] += 1
            elif score >= 50:
                score_ranges["50-64"] += 1
            else:
                score_ranges["0-49"] += 1

            all_matched_skills.extend(ranking.matched_skills or [])
            all_missing_skills.extend(ranking.missing_skills or [])

        # Count skill frequencies
        from collections import Counter
        top_skills = Counter(all_matched_skills).most_common(10)
        common_missing_skills = Counter(all_missing_skills).most_common(10)

        return {
            "total_candidates": total,
            "average_score": round(avg_score, 2),
            "score_distribution": score_ranges,
            "top_skills": [{"skill": skill, "count": count} for skill, count in top_skills],
            "common_missing_skills": [{"skill": skill, "count": count} for skill, count in common_missing_skills],
            "top_candidate_score": max(r.overall_score for r in rankings),
            "lowest_candidate_score": min(r.overall_score for r in rankings)
        }
