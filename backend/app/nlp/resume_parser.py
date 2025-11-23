"""Resume parsing and information extraction."""

import re
from typing import Dict, List, Optional
import spacy
from datetime import datetime
from loguru import logger


class ResumeParser:
    """Parse resumes and extract structured information."""

    def __init__(self):
        """Initialize resume parser with NLP model."""
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("spaCy model loaded successfully")
        except OSError:
            logger.warning("spaCy model not found. Downloading...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")

        # Skill database (expandable)
        self.skills_database = self._load_skills_database()

    def _load_skills_database(self) -> set:
        """Load comprehensive skills database.

        Returns:
            Set of known skills
        """
        skills = {
            # Programming Languages
            "python", "java", "javascript", "typescript", "c++", "c#", "ruby", "go",
            "rust", "php", "swift", "kotlin", "scala", "r", "matlab", "perl", "bash",

            # Web Technologies
            "html", "css", "react", "angular", "vue", "node.js", "express", "django",
            "flask", "fastapi", "spring", "asp.net", "jquery", "bootstrap", "tailwind",

            # Databases
            "sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch",
            "oracle", "sqlite", "cassandra", "dynamodb", "firebase",

            # Cloud & DevOps
            "aws", "azure", "gcp", "docker", "kubernetes", "jenkins", "gitlab",
            "github actions", "terraform", "ansible", "ci/cd", "devops",

            # Data Science & ML
            "machine learning", "deep learning", "nlp", "computer vision", "tensorflow",
            "pytorch", "scikit-learn", "pandas", "numpy", "matplotlib", "keras",
            "data analysis", "statistics", "data visualization", "tableau", "power bi",

            # Tools & Frameworks
            "git", "jira", "confluence", "slack", "agile", "scrum", "kanban",
            "rest api", "graphql", "microservices", "oauth", "jwt",

            # Soft Skills
            "leadership", "communication", "teamwork", "problem solving",
            "analytical thinking", "project management", "time management",
        }
        return skills

    def parse(self, text: str) -> Dict:
        """Parse resume text and extract structured information.

        Args:
            text: Resume text content

        Returns:
            Dictionary containing parsed resume information
        """
        doc = self.nlp(text)

        parsed_data = {
            "name": self._extract_name(text, doc),
            "email": self._extract_email(text),
            "phone": self._extract_phone(text),
            "skills": self._extract_skills(text),
            "education": self._extract_education(text, doc),
            "experience": self._extract_experience(text),
            "total_experience_years": self._calculate_total_experience(text),
        }

        logger.info(f"Parsed resume: {len(parsed_data['skills'])} skills found")
        return parsed_data

    def _extract_name(self, text: str, doc: spacy.tokens.Doc) -> Optional[str]:
        """Extract candidate name from resume.

        Args:
            text: Resume text
            doc: spaCy document

        Returns:
            Candidate name or None
        """
        # Try to find name from first few lines (usually at top)
        lines = text.split("\n")[:5]
        for line in lines:
            line = line.strip()
            if len(line.split()) >= 2 and len(line.split()) <= 4:
                # Check if it looks like a name (capitalized words)
                if all(word[0].isupper() for word in line.split() if word):
                    return line

        # Fallback: Use NER to find PERSON entities
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                return ent.text

        return None

    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email address from resume.

        Args:
            text: Resume text

        Returns:
            Email address or None
        """
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        matches = re.findall(email_pattern, text)
        return matches[0] if matches else None

    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number from resume.

        Args:
            text: Resume text

        Returns:
            Phone number or None
        """
        # Match various phone formats
        phone_patterns = [
            r"\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
            r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
        ]

        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]

        return None

    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills from resume.

        Args:
            text: Resume text

        Returns:
            List of identified skills
        """
        text_lower = text.lower()
        found_skills = []

        for skill in self.skills_database:
            # Use word boundaries for better matching
            pattern = r"\b" + re.escape(skill) + r"\b"
            if re.search(pattern, text_lower):
                found_skills.append(skill)

        return sorted(list(set(found_skills)))

    def _extract_education(self, text: str, doc: spacy.tokens.Doc) -> List[Dict]:
        """Extract education information from resume.

        Args:
            text: Resume text
            doc: spaCy document

        Returns:
            List of education entries
        """
        education = []
        education_keywords = [
            "education", "academic", "qualification", "degree", "university",
            "college", "school", "bachelor", "master", "phd", "doctorate"
        ]

        degrees = {
            "phd", "ph.d", "doctorate", "doctor of philosophy",
            "master", "m.s.", "m.sc", "mba", "m.a.",
            "bachelor", "b.s.", "b.sc", "b.a.", "b.tech", "b.e.",
            "associate", "diploma"
        }

        lines = text.split("\n")
        text_lower = text.lower()

        # Find education section
        in_education_section = False
        for i, line in enumerate(lines):
            line_lower = line.lower()

            if any(keyword in line_lower for keyword in education_keywords):
                in_education_section = True

            if in_education_section:
                # Look for degree mentions
                for degree in degrees:
                    if degree in line_lower:
                        # Try to find year
                        year_match = re.search(r"(19|20)\d{2}", line)
                        year = year_match.group() if year_match else None

                        education.append({
                            "degree": degree.title(),
                            "year": year,
                            "institution": self._find_institution(line, doc)
                        })

                # Stop if we hit another major section
                if any(section in line_lower for section in ["experience", "work history", "skills", "projects"]):
                    break

        return education[:5]  # Limit to 5 entries

    def _find_institution(self, text: str, doc: spacy.tokens.Doc) -> Optional[str]:
        """Find educational institution name.

        Args:
            text: Text to search
            doc: spaCy document

        Returns:
            Institution name or None
        """
        # Look for ORG entities that might be institutions
        mini_doc = self.nlp(text)
        for ent in mini_doc.ents:
            if ent.label_ == "ORG":
                return ent.text
        return None

    def _extract_experience(self, text: str) -> List[Dict]:
        """Extract work experience from resume.

        Args:
            text: Resume text

        Returns:
            List of work experience entries
        """
        experience = []
        experience_keywords = [
            "experience", "work history", "employment", "professional experience",
            "work experience", "career"
        ]

        lines = text.split("\n")

        # Find experience section
        in_experience_section = False
        for line in lines:
            line_lower = line.lower()

            if any(keyword in line_lower for keyword in experience_keywords):
                in_experience_section = True

            if in_experience_section:
                # Look for date ranges (e.g., "2020-2023", "Jan 2020 - Present")
                date_patterns = [
                    r"(19|20)\d{2}\s*-\s*(19|20)\d{2}",
                    r"(19|20)\d{2}\s*-\s*present",
                    r"\w+\s+(19|20)\d{2}\s*-\s*\w+\s+(19|20)\d{2}",
                ]

                for pattern in date_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        experience.append({
                            "description": line.strip(),
                            "dates": re.search(pattern, line, re.IGNORECASE).group()
                        })

                # Stop if we hit another major section
                if any(section in line_lower for section in ["education", "skills", "projects", "certifications"]):
                    break

        return experience[:10]  # Limit to 10 entries

    def _calculate_total_experience(self, text: str) -> float:
        """Calculate total years of experience.

        Args:
            text: Resume text

        Returns:
            Total years of experience
        """
        current_year = datetime.now().year
        years = re.findall(r"(19|20)\d{2}", text)

        if years:
            years = [int(y) for y in years]
            min_year = min(years)
            # Estimate: difference between current year and earliest mentioned year
            total_years = current_year - min_year
            # Cap at reasonable maximum (40 years)
            return min(total_years, 40.0)

        return 0.0
