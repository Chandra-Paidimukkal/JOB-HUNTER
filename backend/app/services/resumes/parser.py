"""
Resume Parser — extracts text from PDF and DOCX files.
Uses PyMuPDF for PDF and python-docx for DOCX.
"""
import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF using PyMuPDF."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text("text"))
        doc.close()
        return "\n".join(text_parts).strip()
    except ImportError:
        raise RuntimeError("PyMuPDF not installed. Run: pip install PyMuPDF")
    except Exception as e:
        logger.error(f"PDF extraction error for {file_path}: {e}")
        raise ValueError(f"Could not extract text from PDF: {str(e)}")


def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX using python-docx."""
    try:
        from docx import Document
        doc = Document(file_path)
        text_parts = []

        # Main paragraphs
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text.strip())

        # Tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip():
                        text_parts.append(cell.text.strip())

        return "\n".join(text_parts).strip()
    except ImportError:
        raise RuntimeError("python-docx not installed. Run: pip install python-docx")
    except Exception as e:
        logger.error(f"DOCX extraction error for {file_path}: {e}")
        raise ValueError(f"Could not extract text from DOCX: {str(e)}")


def extract_resume_text(file_path: str, file_type: str) -> str:
    """Route to correct parser based on file type."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    file_size = os.path.getsize(file_path)
    if file_size == 0:
        raise ValueError("Uploaded file is empty")

    file_type = file_type.lower().strip(".")
    if file_type == "pdf":
        return extract_text_from_pdf(file_path)
    elif file_type in ("docx", "doc"):
        return extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}. Only PDF and DOCX are supported.")


def validate_resume_file(file_path: str, file_type: str, max_size_mb: int = 10) -> None:
    """Validate uploaded resume file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError("File not found")

    # Size check
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > max_size_mb:
        raise ValueError(f"File size {size_mb:.1f}MB exceeds maximum {max_size_mb}MB")

    # Type check
    allowed = {".pdf", ".docx", ".doc"}
    if path.suffix.lower() not in allowed:
        raise ValueError(f"File type {path.suffix} not allowed. Use PDF or DOCX.")

    # Minimal content check
    text = extract_resume_text(file_path, file_type)
    if len(text.strip()) < 100:
        raise ValueError("Resume appears to be empty or contains too little text")
