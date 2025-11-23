"""Interview question generator using NLP."""

from typing import Dict, List
import random
from loguru import logger


class InterviewQuestionGenerator:
    """Generate interview questions based on resume and job description."""

    def __init__(self):
        """Initialize question generator."""
        self.question_templates = self._load_question_templates()

    def _load_question_templates(self) -> Dict:
        """Load question templates by category."""
        return {
            "technical_skills": [
                "Can you walk me through a project where you used {skill}?",
                "How would you explain {skill} to a non-technical person?",
                "What challenges have you faced while working with {skill}?",
                "Describe a situation where {skill} was crucial to project success.",
                "How do you stay current with {skill} developments?",
            ],
            "experience": [
                "Tell me about a time when you {achievement}.",
                "Describe your most challenging project and how you overcame obstacles.",
                "How did you handle {situation} in your previous role?",
                "What was your biggest accomplishment at {company}?",
                "Walk me through your typical day at {company}.",
            ],
            "leadership": [
                "Describe a time when you led a team through a difficult situation.",
                "How do you handle conflicts within your team?",
                "Tell me about a time you mentored someone.",
                "How do you motivate team members?",
                "Describe your leadership style.",
            ],
            "problem_solving": [
                "Tell me about a complex problem you solved.",
                "Describe a time when you had to make a decision with limited information.",
                "How do you approach debugging a difficult issue?",
                "Walk me through your problem-solving process.",
                "Tell me about a time you failed and what you learned.",
            ],
            "behavioral": [
                "Why are you interested in this position?",
                "Where do you see yourself in 5 years?",
                "What motivates you in your work?",
                "How do you handle stress and pressure?",
                "Describe a time you had to learn something quickly.",
            ],
            "cultural_fit": [
                "What type of work environment do you thrive in?",
                "How do you prefer to receive feedback?",
                "What's important to you in a company culture?",
                "How do you balance multiple priorities?",
                "What are you looking for in your next role?",
            ]
        }

    def generate_questions(
        self,
        resume_data: Dict,
        job_data: Dict,
        num_questions: int = 15
    ) -> List[Dict]:
        """Generate personalized interview questions.

        Args:
            resume_data: Parsed resume data
            job_data: Parsed job data
            num_questions: Number of questions to generate

        Returns:
            List of interview questions with metadata
        """
        questions = []

        # Technical skills questions (40%)
        skills = resume_data.get("skills", [])
        required_skills = job_data.get("required_skills", [])

        # Prioritize required skills
        relevant_skills = list(set(skills).intersection(set(required_skills)))
        if not relevant_skills:
            relevant_skills = skills[:5]  # Use top skills from resume

        technical_count = int(num_questions * 0.4)
        for i in range(min(technical_count, len(relevant_skills))):
            skill = relevant_skills[i]
            template = random.choice(self.question_templates["technical_skills"])
            questions.append({
                "category": "technical_skills",
                "question": template.format(skill=skill),
                "difficulty": "medium",
                "focus_area": skill,
                "why_asked": f"This question assesses expertise in {skill}, which is required for this role."
            })

        # Experience questions (25%)
        experience_count = int(num_questions * 0.25)
        experience_templates = self.question_templates["experience"]
        for i in range(experience_count):
            template = random.choice(experience_templates)
            # Try to personalize with actual experience
            experience_items = resume_data.get("experience", [])
            if experience_items and "{company}" in template:
                company = self._extract_company(experience_items[0].get("description", ""))
                question = template.format(company=company if company else "your previous company")
            else:
                question = template.format(
                    achievement="improved a process or system",
                    situation="a difficult technical challenge"
                )

            questions.append({
                "category": "experience",
                "question": question,
                "difficulty": "medium",
                "focus_area": "past experience",
                "why_asked": "This question evaluates your practical experience and problem-solving approach."
            })

        # Leadership questions (15%) - if leadership indicators found
        leadership_indicators = resume_data.get("leadership_indicators", [])
        if leadership_indicators or len(resume_data.get("experience", [])) > 2:
            leadership_count = int(num_questions * 0.15)
            for i in range(leadership_count):
                template = random.choice(self.question_templates["leadership"])
                questions.append({
                    "category": "leadership",
                    "question": template,
                    "difficulty": "hard",
                    "focus_area": "leadership",
                    "why_asked": "This assesses your leadership capabilities and team management skills."
                })

        # Problem-solving questions (10%)
        problem_count = int(num_questions * 0.10)
        for i in range(problem_count):
            template = random.choice(self.question_templates["problem_solving"])
            questions.append({
                "category": "problem_solving",
                "question": template,
                "difficulty": "hard",
                "focus_area": "analytical thinking",
                "why_asked": "This evaluates your problem-solving methodology and critical thinking."
            })

        # Behavioral questions (5%)
        behavioral_count = int(num_questions * 0.05)
        for i in range(behavioral_count):
            template = random.choice(self.question_templates["behavioral"])
            questions.append({
                "category": "behavioral",
                "question": template,
                "difficulty": "easy",
                "focus_area": "motivation and goals",
                "why_asked": "This helps understand your career goals and motivations."
            })

        # Cultural fit questions (5%)
        remaining = num_questions - len(questions)
        for i in range(remaining):
            template = random.choice(self.question_templates["cultural_fit"])
            questions.append({
                "category": "cultural_fit",
                "question": template,
                "difficulty": "easy",
                "focus_area": "cultural alignment",
                "why_asked": "This assesses fit with company culture and values."
            })

        # Shuffle to mix categories
        random.shuffle(questions)

        # Number the questions
        for i, q in enumerate(questions[:num_questions], 1):
            q["number"] = i

        return questions[:num_questions]

    def _extract_company(self, description: str) -> str:
        """Try to extract company name from experience description."""
        # Simple extraction - could be improved
        words = description.split()
        for i, word in enumerate(words):
            if word.lower() in ["at", "@"] and i + 1 < len(words):
                return words[i + 1].strip(",.")
        return ""

    def generate_question_scorecard(self, questions: List[Dict]) -> Dict:
        """Generate a scorecard template for interview evaluation.

        Args:
            questions: List of interview questions

        Returns:
            Scorecard template
        """
        return {
            "candidate_info": {
                "name": "",
                "position": "",
                "interview_date": "",
                "interviewer": ""
            },
            "questions": [
                {
                    "number": q["number"],
                    "question": q["question"],
                    "category": q["category"],
                    "rating": None,  # 1-5 scale
                    "notes": "",
                    "strengths": [],
                    "concerns": []
                }
                for q in questions
            ],
            "overall_assessment": {
                "technical_score": None,
                "cultural_fit_score": None,
                "communication_score": None,
                "overall_score": None,
                "recommendation": "",  # "Strong Hire", "Hire", "No Hire", "Strong No Hire"
                "summary": ""
            }
        }
