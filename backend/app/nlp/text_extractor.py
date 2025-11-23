"""Text extraction from various file formats."""

import re
from pathlib import Path
from typing import Optional
import PyPDF2
import pdfplumber
from docx import Document
from loguru import logger


class TextExtractor:
    """Extract text from various document formats."""

    @staticmethod
    def extract_from_pdf(file_path: str) -> str:
        """Extract text from PDF file.

        Args:
            file_path: Path to PDF file

        Returns:
            Extracted text content

        Raises:
            Exception: If text extraction fails
        """
        text = ""
        try:
            # Try pdfplumber first (better for complex PDFs)
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

            # If no text extracted, try PyPDF2
            if not text.strip():
                with open(file_path, "rb") as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"

            logger.info(f"Extracted {len(text)} characters from PDF: {file_path}")
            return text.strip()

        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {str(e)}")
            raise

    @staticmethod
    def extract_from_docx(file_path: str) -> str:
        """Extract text from DOCX file.

        Args:
            file_path: Path to DOCX file

        Returns:
            Extracted text content

        Raises:
            Exception: If text extraction fails
        """
        try:
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            logger.info(f"Extracted {len(text)} characters from DOCX: {file_path}")
            return text.strip()

        except Exception as e:
            logger.error(f"Error extracting text from DOCX {file_path}: {str(e)}")
            raise

    @staticmethod
    def extract_from_txt(file_path: str) -> str:
        """Extract text from TXT file.

        Args:
            file_path: Path to TXT file

        Returns:
            Extracted text content

        Raises:
            Exception: If text extraction fails
        """
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                text = file.read()
            logger.info(f"Extracted {len(text)} characters from TXT: {file_path}")
            return text.strip()

        except Exception as e:
            logger.error(f"Error extracting text from TXT {file_path}: {str(e)}")
            raise

    @classmethod
    def extract_text(cls, file_path: str) -> str:
        """Extract text from file based on extension.

        Args:
            file_path: Path to file

        Returns:
            Extracted text content

        Raises:
            ValueError: If file type is not supported
            Exception: If text extraction fails
        """
        path = Path(file_path)
        extension = path.suffix.lower()

        extractors = {
            ".pdf": cls.extract_from_pdf,
            ".docx": cls.extract_from_docx,
            ".doc": cls.extract_from_docx,
            ".txt": cls.extract_from_txt,
        }

        if extension not in extractors:
            raise ValueError(f"Unsupported file type: {extension}")

        return extractors[extension](file_path)

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize extracted text.

        Args:
            text: Raw text to clean

        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove special characters but keep important punctuation
        text = re.sub(r"[^\w\s\.\,\-\@\(\)\+\/]", "", text)

        # Normalize line breaks
        text = re.sub(r"\n+", "\n", text)

        return text.strip()
