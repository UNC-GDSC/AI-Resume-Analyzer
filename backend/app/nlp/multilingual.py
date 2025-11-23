"""Multi-language support for NLP processing."""

from typing import Dict, List, Optional
import re
from loguru import logger


class MultiLanguageProcessor:
    """Process resumes and job descriptions in multiple languages."""

    def __init__(self):
        """Initialize multi-language processor."""
        self.supported_languages = {
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "pt": "Portuguese",
            "zh": "Chinese",
        }

        # Language-specific skill databases
        self.language_skills = {
            "en": self._load_english_skills(),
            "es": self._load_spanish_skills(),
            "fr": self._load_french_skills(),
            "de": self._load_german_skills(),
        }

    def _load_english_skills(self) -> set:
        """Load English skill keywords."""
        return {
            "python", "java", "javascript", "react", "docker", "kubernetes",
            "machine learning", "data analysis", "project management"
        }

    def _load_spanish_skills(self) -> set:
        """Load Spanish skill keywords."""
        return {
            "python", "java", "javascript", "react", "docker", "kubernetes",
            "aprendizaje automático", "análisis de datos", "gestión de proyectos",
            "desarrollo web", "base de datos", "inteligencia artificial"
        }

    def _load_french_skills(self) -> set:
        """Load French skill keywords."""
        return {
            "python", "java", "javascript", "react", "docker", "kubernetes",
            "apprentissage automatique", "analyse de données", "gestion de projet",
            "développement web", "base de données", "intelligence artificielle"
        }

    def _load_german_skills(self) -> set:
        """Load German skill keywords."""
        return {
            "python", "java", "javascript", "react", "docker", "kubernetes",
            "maschinelles lernen", "datenanalyse", "projektmanagement",
            "webentwicklung", "datenbank", "künstliche intelligenz"
        }

    def detect_language(self, text: str) -> str:
        """Detect language of text.

        Args:
            text: Input text

        Returns:
            Language code (en, es, fr, de, etc.)
        """
        # Simple language detection based on common words
        text_lower = text.lower()

        # Language indicators
        spanish_indicators = ["años", "experiencia", "empresa", "educación", "habilidades"]
        french_indicators = ["ans", "expérience", "entreprise", "éducation", "compétences"]
        german_indicators = ["jahre", "erfahrung", "unternehmen", "bildung", "fähigkeiten"]

        spanish_count = sum(1 for word in spanish_indicators if word in text_lower)
        french_count = sum(1 for word in french_indicators if word in text_lower)
        german_count = sum(1 for word in german_indicators if word in text_lower)

        if spanish_count > 2:
            return "es"
        elif french_count > 2:
            return "fr"
        elif german_count > 2:
            return "de"
        else:
            return "en"  # Default to English

    def extract_multilingual_skills(self, text: str, language: str = None) -> List[str]:
        """Extract skills from text in detected language.

        Args:
            text: Input text
            language: Language code (auto-detect if None)

        Returns:
            List of extracted skills
        """
        if language is None:
            language = self.detect_language(text)

        if language not in self.language_skills:
            language = "en"  # Fallback to English

        skills_db = self.language_skills[language]
        text_lower = text.lower()

        found_skills = []
        for skill in skills_db:
            if skill in text_lower:
                found_skills.append(skill)

        return sorted(list(set(found_skills)))

    def translate_field_names(self, field: str, language: str) -> str:
        """Translate field names for display.

        Args:
            field: Field name in English
            language: Target language

        Returns:
            Translated field name
        """
        translations = {
            "es": {
                "experience": "experiencia",
                "education": "educación",
                "skills": "habilidades",
                "summary": "resumen",
                "name": "nombre",
                "email": "correo electrónico",
                "phone": "teléfono",
            },
            "fr": {
                "experience": "expérience",
                "education": "éducation",
                "skills": "compétences",
                "summary": "résumé",
                "name": "nom",
                "email": "e-mail",
                "phone": "téléphone",
            },
            "de": {
                "experience": "erfahrung",
                "education": "bildung",
                "skills": "fähigkeiten",
                "summary": "zusammenfassung",
                "name": "name",
                "email": "e-mail",
                "phone": "telefon",
            }
        }

        if language == "en" or language not in translations:
            return field

        return translations[language].get(field, field)
