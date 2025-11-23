"""Tests for NLP modules."""

import pytest
from app.nlp.text_extractor import TextExtractor
from app.nlp.resume_parser import ResumeParser
from app.nlp.job_parser import JobParser
from app.nlp.ranker import ResumeRanker


class TestTextExtractor:
    """Test TextExtractor class."""

    def test_clean_text(self):
        """Test text cleaning."""
        extractor = TextExtractor()
        dirty_text = "This   has    extra    spaces\n\n\nand   newlines"
        clean = extractor.clean_text(dirty_text)
        assert "  " not in clean
        assert clean.strip() == clean


class TestResumeParser:
    """Test ResumeParser class."""

    def test_extract_email(self):
        """Test email extraction."""
        parser = ResumeParser()
        text = "Contact me at john.doe@example.com for more info"
        email = parser._extract_email(text)
        assert email == "john.doe@example.com"

    def test_extract_phone(self):
        """Test phone extraction."""
        parser = ResumeParser()
        text = "Call me at (555) 123-4567"
        phone = parser._extract_phone(text)
        assert phone is not None
        assert "555" in phone

    def test_extract_skills(self):
        """Test skill extraction."""
        parser = ResumeParser()
        text = "I have experience with Python, JavaScript, and React"
        skills = parser._extract_skills(text)
        assert "python" in skills
        assert "javascript" in skills
        assert "react" in skills


class TestJobParser:
    """Test JobParser class."""

    def test_extract_experience_requirement(self):
        """Test experience requirement extraction."""
        parser = JobParser()
        text = "We require 5 years of experience in software development"
        years = parser._extract_experience_requirement(text)
        assert years == 5

    def test_extract_education_requirement(self):
        """Test education requirement extraction."""
        parser = JobParser()
        text = "Bachelor's degree in Computer Science required"
        education = parser._extract_education_requirement(text)
        assert education == "bachelor"


class TestResumeRanker:
    """Test ResumeRanker class."""

    def test_compute_skill_match_score(self):
        """Test skill matching score."""
        ranker = ResumeRanker()
        resume_skills = ["python", "javascript", "react", "node.js"]
        required_skills = ["python", "javascript", "docker"]
        preferred_skills = ["react"]

        score, details = ranker.compute_skill_match_score(
            resume_skills, required_skills, preferred_skills
        )

        assert 0 <= score <= 100
        assert "matched_skills" in details
        assert "missing_skills" in details
        assert "python" in details["matched_skills"]
        assert "javascript" in details["matched_skills"]
        assert "docker" in details["missing_skills"]

    def test_compute_experience_score(self):
        """Test experience scoring."""
        ranker = ResumeRanker()

        # Meets requirement
        score1 = ranker.compute_experience_score(5.0, 5)
        assert score1 >= 100

        # Below requirement
        score2 = ranker.compute_experience_score(3.0, 5)
        assert score2 < 100

    def test_compute_education_score(self):
        """Test education scoring."""
        ranker = ResumeRanker()

        # Bachelor's degree
        education = [{"degree": "Bachelor of Science"}]
        score = ranker.compute_education_score(education, "bachelor")
        assert score == 100.0
