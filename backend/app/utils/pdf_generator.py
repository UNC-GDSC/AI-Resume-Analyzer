"""PDF report generation utilities."""

from typing import Dict, List, Optional
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, PageBreak, Image, KeepTogether
)
from reportlab.lib.colors import HexColor
from loguru import logger


class PDFReportGenerator:
    """Generate professional PDF reports for resume analysis."""

    def __init__(self):
        """Initialize PDF generator."""
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=HexColor('#1a202c'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        # Section heading
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=HexColor('#2d3748'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))

        # Subsection heading
        self.styles.add(ParagraphStyle(
            name='SubsectionHeading',
            parent=self.styles['Heading3'],
            fontSize=13,
            textColor=HexColor('#4a5568'),
            spaceAfter=8,
            spaceBefore=8,
            fontName='Helvetica-Bold'
        ))

        # Body text
        self.styles.add(ParagraphStyle(
            name='BodyText',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=HexColor('#2d3748'),
            spaceAfter=6,
            leading=14
        ))

    def generate_candidate_report(
        self,
        candidate_data: Dict,
        ranking_data: Dict,
        job_data: Dict,
        skill_gap_analysis: Optional[Dict] = None,
        quality_analysis: Optional[Dict] = None
    ) -> BytesIO:
        """Generate comprehensive candidate analysis report.

        Args:
            candidate_data: Candidate/resume information
            ranking_data: Ranking scores and details
            job_data: Job information
            skill_gap_analysis: Optional skill gap analysis
            quality_analysis: Optional resume quality analysis

        Returns:
            BytesIO buffer containing PDF
        """
        try:
            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18,
            )

            # Build document content
            story = []

            # Title
            story.append(Paragraph("Candidate Analysis Report", self.styles['CustomTitle']))
            story.append(Spacer(1, 0.2 * inch))

            # Report metadata
            metadata = [
                ["Report Date:", datetime.now().strftime("%B %d, %Y")],
                ["Job Position:", job_data.get("title", "N/A")],
                ["Candidate:", candidate_data.get("filename", "N/A")]
            ]
            metadata_table = Table(metadata, colWidths=[2 * inch, 4 * inch])
            metadata_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            story.append(metadata_table)
            story.append(Spacer(1, 0.3 * inch))

            # Overall Score Section
            story.append(Paragraph("Overall Assessment", self.styles['SectionHeading']))
            overall_score = ranking_data.get("overall_score", 0)
            score_color = self._get_score_color(overall_score)

            score_data = [
                ["Overall Match Score", f"{overall_score:.1f}/100", self._get_score_label(overall_score)],
            ]
            score_table = Table(score_data, colWidths=[2.5 * inch, 1.5 * inch, 2 * inch])
            score_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#f7fafc')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('TEXTCOLOR', (1, 0), (1, 0), score_color),
                ('ALIGN', (1, 0), (-1, 0), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, HexColor('#f7fafc')]),
            ]))
            story.append(score_table)
            story.append(Spacer(1, 0.2 * inch))

            # Score Breakdown
            story.append(Paragraph("Score Breakdown", self.styles['SubsectionHeading']))
            breakdown_data = [
                ["Category", "Score", "Weight"],
                ["Semantic Similarity", f"{ranking_data.get('semantic_similarity_score', 0):.1f}", "40%"],
                ["Skill Match", f"{ranking_data.get('skill_match_score', 0):.1f}", "30%"],
                ["Experience", f"{ranking_data.get('experience_score', 0):.1f}", "20%"],
                ["Education", f"{ranking_data.get('education_score', 0):.1f}", "10%"],
            ]
            breakdown_table = Table(breakdown_data, colWidths=[2.5 * inch, 1.5 * inch, 1.5 * inch])
            breakdown_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2d3748')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor('#f7fafc')]),
            ]))
            story.append(breakdown_table)
            story.append(Spacer(1, 0.3 * inch))

            # Skills Analysis
            story.append(Paragraph("Skills Analysis", self.styles['SectionHeading']))

            matched_skills = ranking_data.get("matched_skills", [])
            missing_skills = ranking_data.get("missing_skills", [])

            if matched_skills:
                story.append(Paragraph("✓ Matched Skills", self.styles['SubsectionHeading']))
                skills_text = ", ".join(matched_skills[:15])  # Limit to 15
                story.append(Paragraph(skills_text, self.styles['BodyText']))
                story.append(Spacer(1, 0.1 * inch))

            if missing_skills:
                story.append(Paragraph("✗ Missing Skills", self.styles['SubsectionHeading']))
                missing_text = ", ".join(missing_skills[:10])  # Limit to 10
                story.append(Paragraph(missing_text, self.styles['BodyText']))
                story.append(Spacer(1, 0.3 * inch))

            # Skill Gap Analysis (if provided)
            if skill_gap_analysis:
                story.append(PageBreak())
                story.append(Paragraph("Skill Gap Analysis", self.styles['SectionHeading']))

                gaps = skill_gap_analysis.get("gaps", {})
                trainability = skill_gap_analysis.get("trainability_assessment", {})

                # Trainability score
                train_data = [
                    ["Trainability Score", f"{trainability.get('score', 0):.1f}/100"],
                    ["Assessment", trainability.get("level", "N/A")],
                    ["Recommendation", trainability.get("recommendation", "N/A")],
                ]
                train_table = Table(train_data, colWidths=[2 * inch, 4 * inch])
                train_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), HexColor('#f7fafc')),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                story.append(train_table)
                story.append(Spacer(1, 0.2 * inch))

                # Learning paths
                learning_paths = skill_gap_analysis.get("learning_paths", [])
                if learning_paths:
                    story.append(Paragraph("Recommended Learning Paths", self.styles['SubsectionHeading']))

                    for i, path in enumerate(learning_paths[:5], 1):  # Top 5
                        path_text = (
                            f"<b>{i}. {path.get('skill', '').title()}</b> "
                            f"({path.get('priority', 'Medium')} Priority)<br/>"
                            f"Difficulty: {path.get('difficulty', 'N/A')} | "
                            f"Time: {path.get('estimated_time', 'N/A')}<br/>"
                            f"Resources: {', '.join(path.get('learning_resources', [])[:3])}"
                        )
                        story.append(Paragraph(path_text, self.styles['BodyText']))
                        story.append(Spacer(1, 0.1 * inch))

            # Quality Analysis (if provided)
            if quality_analysis:
                story.append(PageBreak())
                story.append(Paragraph("Resume Quality Analysis", self.styles['SectionHeading']))

                quality_score = quality_analysis.get("overall_score", 0)
                quality_tier = quality_analysis.get("overall_quality_tier", "N/A")

                quality_data = [
                    ["Overall Quality Score", f"{quality_score:.1f}/100"],
                    ["Quality Tier", quality_tier],
                ]

                # Add individual scores
                scores = quality_analysis.get("scores", {})
                for category, score in scores.items():
                    quality_data.append([category.replace("_", " ").title(), f"{score:.1f}"])

                quality_table = Table(quality_data, colWidths=[2.5 * inch, 2 * inch])
                quality_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), HexColor('#f7fafc')),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                story.append(quality_table)
                story.append(Spacer(1, 0.2 * inch))

                # Suggestions
                suggestions = quality_analysis.get("suggestions", [])
                if suggestions:
                    story.append(Paragraph("Improvement Suggestions", self.styles['SubsectionHeading']))
                    for suggestion in suggestions[:5]:
                        story.append(Paragraph(f"• {suggestion}", self.styles['BodyText']))

            # Footer
            story.append(Spacer(1, 0.5 * inch))
            footer_text = (
                f"<i>Generated by AI Resume Analyzer on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</i>"
            )
            story.append(Paragraph(footer_text, self.styles['BodyText']))

            # Build PDF
            doc.build(story)
            buffer.seek(0)

            logger.info(f"Generated candidate report PDF for {candidate_data.get('filename', 'unknown')}")

            return buffer

        except Exception as e:
            logger.error(f"Error generating PDF report: {str(e)}")
            raise

    def generate_pool_summary_report(
        self,
        job_data: Dict,
        rankings: List[Dict],
        pool_quality: Dict,
        skill_gaps: Optional[Dict] = None
    ) -> BytesIO:
        """Generate summary report for entire candidate pool.

        Args:
            job_data: Job information
            rankings: List of all rankings
            pool_quality: Pool quality analysis
            skill_gaps: Optional pool-wide skill gap analysis

        Returns:
            BytesIO buffer containing PDF
        """
        try:
            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18,
            )

            story = []

            # Title
            story.append(Paragraph("Candidate Pool Summary Report", self.styles['CustomTitle']))
            story.append(Spacer(1, 0.2 * inch))

            # Metadata
            metadata = [
                ["Report Date:", datetime.now().strftime("%B %d, %Y")],
                ["Job Position:", job_data.get("title", "N/A")],
                ["Total Candidates:", str(len(rankings))],
            ]
            metadata_table = Table(metadata, colWidths=[2 * inch, 4 * inch])
            metadata_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
            ]))
            story.append(metadata_table)
            story.append(Spacer(1, 0.3 * inch))

            # Pool Quality
            story.append(Paragraph("Pool Quality Assessment", self.styles['SectionHeading']))

            quality_tier = pool_quality.get("quality_tier", "N/A")
            quality_desc = pool_quality.get("quality_description", "N/A")

            story.append(Paragraph(f"<b>Quality Tier:</b> {quality_tier}", self.styles['BodyText']))
            story.append(Paragraph(f"<b>Assessment:</b> {quality_desc}", self.styles['BodyText']))
            story.append(Spacer(1, 0.2 * inch))

            # Statistics
            stats = pool_quality.get("statistics", {})
            stats_data = [
                ["Metric", "Value"],
                ["Average Score", f"{stats.get('average_score', 0):.2f}"],
                ["Median Score", f"{stats.get('median_score', 0):.2f}"],
                ["Highest Score", f"{stats.get('top_score', 0):.2f}"],
                ["Lowest Score", f"{stats.get('lowest_score', 0):.2f}"],
            ]
            stats_table = Table(stats_data, colWidths=[2.5 * inch, 2 * inch])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2d3748')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor('#f7fafc')]),
            ]))
            story.append(stats_table)
            story.append(Spacer(1, 0.3 * inch))

            # Top Candidates
            story.append(Paragraph("Top Candidates", self.styles['SectionHeading']))
            top_candidates = sorted(rankings, key=lambda x: x.get("overall_score", 0), reverse=True)[:10]

            top_data = [["Rank", "Candidate", "Overall Score", "Skill Match"]]
            for i, candidate in enumerate(top_candidates, 1):
                top_data.append([
                    str(i),
                    candidate.get("resume_filename", "Unknown")[:30],
                    f"{candidate.get('overall_score', 0):.1f}",
                    f"{candidate.get('skill_match_score', 0):.1f}"
                ])

            top_table = Table(top_data, colWidths=[0.6 * inch, 2.5 * inch, 1.2 * inch, 1.2 * inch])
            top_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2d3748')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor('#f7fafc')]),
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
            ]))
            story.append(top_table)

            # Footer
            story.append(Spacer(1, 0.5 * inch))
            footer_text = (
                f"<i>Generated by AI Resume Analyzer on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</i>"
            )
            story.append(Paragraph(footer_text, self.styles['BodyText']))

            # Build PDF
            doc.build(story)
            buffer.seek(0)

            logger.info(f"Generated pool summary report PDF for job {job_data.get('title', 'unknown')}")

            return buffer

        except Exception as e:
            logger.error(f"Error generating pool summary PDF: {str(e)}")
            raise

    def _get_score_color(self, score: float) -> HexColor:
        """Get color for score."""
        if score >= 80:
            return HexColor('#38a169')  # Green
        elif score >= 65:
            return HexColor('#3182ce')  # Blue
        elif score >= 50:
            return HexColor('#d69e2e')  # Yellow
        else:
            return HexColor('#e53e3e')  # Red

    def _get_score_label(self, score: float) -> str:
        """Get label for score."""
        if score >= 80:
            return "Excellent Match"
        elif score >= 65:
            return "Good Match"
        elif score >= 50:
            return "Moderate Match"
        else:
            return "Poor Match"
