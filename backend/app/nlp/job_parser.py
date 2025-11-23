"""Job description parsing and information extraction."""

import re
from typing import Dict, List, Optional
import spacy
from loguru import logger


class JobParser:
    """Parse job descriptions and extract requirements."""

    def __init__(self):
        """Initialize job parser with NLP model."""
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("Job parser initialized with spaCy model")
        except OSError:
            logger.warning("spaCy model not found. Downloading...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")

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
            "sql", "nosql",

            # Web Technologies
            "html", "css", "react", "angular", "vue", "node.js", "express", "django",
            "flask", "fastapi", "spring", "asp.net", "jquery", "bootstrap", "tailwind",
            "webpack", "babel", "sass", "less",

            # Databases
            "mysql", "postgresql", "mongodb", "redis", "elasticsearch",
            "oracle", "sqlite", "cassandra", "dynamodb", "firebase", "mariadb",

            # Cloud & DevOps
            "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "jenkins",
            "gitlab", "github actions", "terraform", "ansible", "ci/cd", "devops",
            "linux", "unix", "windows server",

            # Data Science & ML
            "machine learning", "deep learning", "nlp", "natural language processing",
            "computer vision", "tensorflow", "pytorch", "scikit-learn", "pandas",
            "numpy", "matplotlib", "keras", "data analysis", "statistics",
            "data visualization", "tableau", "power bi", "jupyter", "spark",

            # Mobile
            "ios", "android", "react native", "flutter", "xamarin",

            # Testing
            "unit testing", "integration testing", "test automation", "selenium",
            "jest", "pytest", "junit", "tdd", "bdd",

            # Tools & Frameworks
            "git", "svn", "jira", "confluence", "slack", "agile", "scrum", "kanban",
            "rest api", "graphql", "soap", "microservices", "oauth", "jwt", "websocket",

            # Soft Skills
            "leadership", "communication", "teamwork", "problem solving",
            "analytical thinking", "project management", "time management",
            "critical thinking", "collaboration", "mentoring",
        }
        return skills

    def parse(self, title: str, description: str) -> Dict:
        """Parse job description and extract requirements.

        Args:
            title: Job title
            description: Job description text

        Returns:
            Dictionary containing parsed job information
        """
        full_text = f"{title}\n{description}"
        doc = self.nlp(description)

        parsed_data = {
            "required_skills": self._extract_required_skills(full_text),
            "preferred_skills": self._extract_preferred_skills(full_text),
            "education_level": self._extract_education_requirement(description),
            "experience_years": self._extract_experience_requirement(description),
            "key_responsibilities": self._extract_responsibilities(description),
        }

        logger.info(
            f"Parsed job: {len(parsed_data['required_skills'])} required skills, "
            f"{len(parsed_data['preferred_skills'])} preferred skills"
        )
        return parsed_data

    def _extract_required_skills(self, text: str) -> List[str]:
        """Extract required skills from job description.

        Args:
            text: Job description text

        Returns:
            List of required skills
        """
        text_lower = text.lower()
        required_skills = []

        # Look for required skills section
        required_section_patterns = [
            r"required skills?:?(.*?)(?:preferred|nice|bonus|responsibilities|qualifications|$)",
            r"must have:?(.*?)(?:preferred|nice|bonus|responsibilities|qualifications|$)",
            r"requirements?:?(.*?)(?:preferred|nice|bonus|responsibilities|qualifications|$)",
        ]

        required_text = text_lower
        for pattern in required_section_patterns:
            match = re.search(pattern, text_lower, re.DOTALL | re.IGNORECASE)
            if match:
                required_text = match.group(1)
                break

        # Extract skills from the text
        for skill in self.skills_database:
            pattern = r"\b" + re.escape(skill) + r"\b"
            if re.search(pattern, required_text):
                required_skills.append(skill)

        return sorted(list(set(required_skills)))

    def _extract_preferred_skills(self, text: str) -> List[str]:
        """Extract preferred/nice-to-have skills from job description.

        Args:
            text: Job description text

        Returns:
            List of preferred skills
        """
        text_lower = text.lower()
        preferred_skills = []

        # Look for preferred skills section
        preferred_section_patterns = [
            r"preferred skills?:?(.*?)(?:required|must|responsibilities|qualifications|$)",
            r"nice to have:?(.*?)(?:required|must|responsibilities|qualifications|$)",
            r"bonus:?(.*?)(?:required|must|responsibilities|qualifications|$)",
            r"plus:?(.*?)(?:required|must|responsibilities|qualifications|$)",
        ]

        preferred_text = ""
        for pattern in preferred_section_patterns:
            match = re.search(pattern, text_lower, re.DOTALL | re.IGNORECASE)
            if match:
                preferred_text = match.group(1)
                break

        # Extract skills from the preferred section
        if preferred_text:
            for skill in self.skills_database:
                pattern = r"\b" + re.escape(skill) + r"\b"
                if re.search(pattern, preferred_text):
                    preferred_skills.append(skill)

        return sorted(list(set(preferred_skills)))

    def _extract_education_requirement(self, text: str) -> Optional[str]:
        """Extract education level requirement.

        Args:
            text: Job description text

        Returns:
            Education level or None
        """
        text_lower = text.lower()

        education_levels = {
            "phd": ["phd", "ph.d", "doctorate", "doctoral"],
            "master": ["master", "m.s.", "m.sc", "mba", "m.a.", "ms", "ma"],
            "bachelor": ["bachelor", "b.s.", "b.sc", "b.a.", "b.tech", "b.e.", "bs", "ba"],
            "associate": ["associate"],
            "high school": ["high school", "diploma"],
        }

        for level, keywords in education_levels.items():
            for keyword in keywords:
                pattern = r"\b" + re.escape(keyword) + r"\b"
                if re.search(pattern, text_lower):
                    return level

        return None

    def _extract_experience_requirement(self, text: str) -> Optional[int]:
        """Extract years of experience requirement.

        Args:
            text: Job description text

        Returns:
            Years of experience or None
        """
        # Patterns for experience mentions
        patterns = [
            r"(\d+)\+?\s*years?\s+(?:of\s+)?experience",
            r"(\d+)\+?\s*years?\s+(?:of\s+)?professional\s+experience",
            r"minimum\s+(?:of\s+)?(\d+)\+?\s*years?",
            r"at least\s+(\d+)\+?\s*years?",
        ]

        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return int(match.group(1))

        return None

    def _extract_responsibilities(self, text: str) -> List[str]:
        """Extract key responsibilities from job description.

        Args:
            text: Job description text

        Returns:
            List of responsibilities
        """
        responsibilities = []

        # Look for responsibilities section
        resp_patterns = [
            r"responsibilities:?(.*?)(?:requirements|qualifications|skills|$)",
            r"duties:?(.*?)(?:requirements|qualifications|skills|$)",
            r"you will:?(.*?)(?:requirements|qualifications|skills|$)",
        ]

        resp_text = ""
        for pattern in resp_patterns:
            match = re.search(pattern, text.lower(), re.DOTALL | re.IGNORECASE)
            if match:
                resp_text = match.group(1)
                break

        if resp_text:
            # Split by bullet points or new lines
            lines = re.split(r"[\n\r]+|•|∙|·|-\s+", resp_text)
            for line in lines:
                line = line.strip()
                if len(line) > 20 and len(line) < 500:  # Filter noise
                    responsibilities.append(line)

        return responsibilities[:10]  # Limit to 10 items
