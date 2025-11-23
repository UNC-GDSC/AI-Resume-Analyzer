"""Resume anonymization for bias-free screening."""

import re
from typing import Dict, List, Optional
from loguru import logger


class ResumeAnonymizer:
    """Anonymize resumes to reduce unconscious bias."""

    def __init__(self):
        """Initialize anonymizer."""
        self.sensitive_patterns = self._load_sensitive_patterns()

    def _load_sensitive_patterns(self) -> Dict[str, List]:
        """Load patterns for sensitive information."""
        return {
            "names": [
                r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b",  # First Last
                r"\b[A-Z][a-z]+\s+[A-Z]\.\s+[A-Z][a-z]+\b",  # First M. Last
            ],
            "gender_indicators": [
                r"\b(he|she|him|her|his|hers)\b",
                r"\b(male|female|man|woman|boy|girl)\b",
                r"\b(mr|mrs|ms|miss|sir|madam)\.?\b",
            ],
            "age_indicators": [
                r"\b\d{4}\s*-\s*present\b",  # Birth year ranges
                r"\bborn\s+in\s+\d{4}\b",
                r"\bage:?\s*\d+\b",
                r"\b(19|20)\d{2}\s*-\s*\d{4}\b",  # Date ranges
            ],
            "photos": [
                r"\[?photo\]?",
                r"\[?image\]?",
                r"\[?picture\]?",
            ],
            "addresses": [
                r"\d+\s+[\w\s]+(?:street|st|avenue|ave|road|rd|lane|ln|drive|dr|court|ct|circle|cir)",
                r"\b\d{5}(?:-\d{4})?\b",  # ZIP codes
            ],
            "ethnic_indicators": [
                r"\b(nationality|ethnicity|race|origin):?\s*\w+\b",
            ]
        }

    def anonymize_resume(
        self,
        resume_text: str,
        parsed_data: Dict,
        anonymization_level: str = "standard"
    ) -> Dict:
        """Anonymize resume content.

        Args:
            resume_text: Original resume text
            parsed_data: Parsed resume data
            anonymization_level: "minimal", "standard", or "maximum"

        Returns:
            Anonymized resume data
        """
        anonymized_text = resume_text
        anonymization_log = []

        # Level 1: Minimal - Remove only names and contact info
        if anonymization_level in ["minimal", "standard", "maximum"]:
            anonymized_text, changes = self._remove_personal_identifiers(
                anonymized_text, parsed_data
            )
            anonymization_log.extend(changes)

        # Level 2: Standard - Also remove gender, age, photos
        if anonymization_level in ["standard", "maximum"]:
            anonymized_text, changes = self._remove_demographic_info(anonymized_text)
            anonymization_log.extend(changes)

        # Level 3: Maximum - Also remove addresses, institutions (if not relevant)
        if anonymization_level == "maximum":
            anonymized_text, changes = self._remove_location_info(anonymized_text)
            anonymization_log.extend(changes)

        # Preserve professional content
        anonymized_parsed = self._anonymize_parsed_data(
            parsed_data.copy(), anonymization_level
        )

        return {
            "anonymized_text": anonymized_text,
            "anonymized_data": anonymized_parsed,
            "anonymization_level": anonymization_level,
            "changes_made": len(anonymization_log),
            "change_log": anonymization_log,
            "preserved_content": {
                "skills": True,
                "experience": True,
                "education": True,
                "achievements": True
            }
        }

    def _remove_personal_identifiers(
        self, text: str, parsed_data: Dict
    ) -> tuple:
        """Remove names, emails, phones."""
        changes = []

        # Remove email
        if parsed_data.get("email"):
            text = text.replace(parsed_data["email"], "[EMAIL REDACTED]")
            changes.append("Removed email address")

        # Remove phone
        if parsed_data.get("phone"):
            text = text.replace(parsed_data["phone"], "[PHONE REDACTED]")
            changes.append("Removed phone number")

        # Remove name
        if parsed_data.get("name"):
            name_parts = parsed_data["name"].split()
            for part in name_parts:
                if len(part) > 1:  # Don't replace single letters
                    text = text.replace(part, "[NAME]")
            changes.append("Anonymized candidate name")

        # Remove email patterns
        text = re.sub(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            '[EMAIL REDACTED]',
            text
        )

        # Remove phone patterns
        text = re.sub(
            r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            '[PHONE REDACTED]',
            text
        )

        return text, changes

    def _remove_demographic_info(self, text: str) -> tuple:
        """Remove gender, age, and photo references."""
        changes = []

        # Remove gender pronouns
        gender_replacements = {
            r'\bhe\b': 'they',
            r'\bshe\b': 'they',
            r'\bhim\b': 'them',
            r'\bher\b': 'them',
            r'\bhis\b': 'their',
            r'\bhers\b': 'theirs',
        }

        for pattern, replacement in gender_replacements.items():
            if re.search(pattern, text, re.IGNORECASE):
                text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
                changes.append(f"Neutralized gender pronouns")
                break

        # Remove age indicators
        text = re.sub(r'\bage:?\s*\d+\b', '[AGE REDACTED]', text, flags=re.IGNORECASE)
        text = re.sub(r'\bborn\s+in\s+\d{4}\b', '[DOB REDACTED]', text, flags=re.IGNORECASE)

        if '[AGE REDACTED]' in text or '[DOB REDACTED]' in text:
            changes.append("Removed age/birth year information")

        # Remove photo references
        text = re.sub(r'\[?photo\]?', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\[?image\]?', '', text, flags=re.IGNORECASE)

        return text, changes

    def _remove_location_info(self, text: str) -> tuple:
        """Remove addresses and specific locations."""
        changes = []

        # Remove street addresses
        text = re.sub(
            r'\d+\s+[\w\s]+(?:street|st|avenue|ave|road|rd|lane|ln|drive|dr|court|ct)',
            '[ADDRESS REDACTED]',
            text,
            flags=re.IGNORECASE
        )

        # Remove ZIP codes
        text = re.sub(r'\b\d{5}(?:-\d{4})?\b', '[ZIP REDACTED]', text)

        if '[ADDRESS REDACTED]' in text:
            changes.append("Removed address information")

        return text, changes

    def _anonymize_parsed_data(self, data: Dict, level: str) -> Dict:
        """Anonymize parsed data structure."""
        # Always anonymize
        data["name"] = "Candidate [ANONYMIZED]"
        data["email"] = "[REDACTED]"
        data["phone"] = "[REDACTED]"

        # Standard and maximum: anonymize education institutions
        if level in ["standard", "maximum"]:
            if "education" in data:
                for edu in data["education"]:
                    if "institution" in edu:
                        # Keep degree type but anonymize institution
                        edu["institution"] = "[INSTITUTION REDACTED]"

        # Maximum: also remove exact years (keep only duration)
        if level == "maximum":
            if "experience" in data:
                for exp in data["experience"]:
                    if "dates" in exp:
                        # Keep duration but not specific years
                        exp["dates"] = "[DATES REDACTED]"

        return data

    def get_bias_report(self, original_text: str, parsed_data: Dict) -> Dict:
        """Generate report on potential bias indicators in resume.

        Args:
            original_text: Original resume text
            parsed_data: Parsed resume data

        Returns:
            Bias indicator report
        """
        indicators = {
            "name_present": bool(parsed_data.get("name")),
            "gender_indicators": self._detect_gender_indicators(original_text),
            "age_indicators": self._detect_age_indicators(original_text),
            "photo_present": self._detect_photo_references(original_text),
            "location_specific": self._detect_location_info(original_text),
            "ethnic_indicators": self._detect_ethnic_indicators(original_text)
        }

        # Calculate bias risk score
        risk_count = sum([
            indicators["name_present"],
            len(indicators["gender_indicators"]) > 0,
            len(indicators["age_indicators"]) > 0,
            indicators["photo_present"],
            len(indicators["ethnic_indicators"]) > 0
        ])

        bias_risk = "Low" if risk_count <= 1 else "Medium" if risk_count <= 3 else "High"

        return {
            "bias_risk_level": bias_risk,
            "indicators_found": indicators,
            "recommendation": self._get_anonymization_recommendation(bias_risk),
            "anonymization_suggested": bias_risk in ["Medium", "High"]
        }

    def _detect_gender_indicators(self, text: str) -> List[str]:
        """Detect gender indicators in text."""
        indicators = []
        for pattern in self.sensitive_patterns["gender_indicators"]:
            matches = re.findall(pattern, text, re.IGNORECASE)
            indicators.extend(matches)
        return list(set(indicators))[:5]  # Limit to 5 examples

    def _detect_age_indicators(self, text: str) -> List[str]:
        """Detect age indicators in text."""
        indicators = []
        for pattern in self.sensitive_patterns["age_indicators"]:
            matches = re.findall(pattern, text, re.IGNORECASE)
            indicators.extend(matches)
        return list(set(indicators))[:3]

    def _detect_photo_references(self, text: str) -> bool:
        """Detect photo references."""
        for pattern in self.sensitive_patterns["photos"]:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _detect_location_info(self, text: str) -> List[str]:
        """Detect specific location information."""
        locations = []
        for pattern in self.sensitive_patterns["addresses"]:
            matches = re.findall(pattern, text, re.IGNORECASE)
            locations.extend(matches)
        return list(set(locations))[:3]

    def _detect_ethnic_indicators(self, text: str) -> List[str]:
        """Detect ethnic/nationality indicators."""
        indicators = []
        for pattern in self.sensitive_patterns["ethnic_indicators"]:
            matches = re.findall(pattern, text, re.IGNORECASE)
            indicators.extend(matches)
        return indicators

    def _get_anonymization_recommendation(self, risk_level: str) -> str:
        """Get recommendation based on bias risk."""
        if risk_level == "High":
            return "Strong recommendation to anonymize this resume before review to reduce unconscious bias"
        elif risk_level == "Medium":
            return "Consider anonymizing this resume for fairer evaluation"
        else:
            return "Low bias risk detected, anonymization optional"
