"""
Resume Service — orchestrates upload, parsing, and AI analysis.
"""
import os
import uuid
import logging
from typing import Optional, Dict
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException, status

from app.core.config import settings
from app.models.resume import Resume
from app.models.user import User
from app.services.resumes.parser import extract_resume_text, validate_resume_file
from app.services.ai.groq_client import analyze_resume

logger = logging.getLogger(__name__)

ALLOWED_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/msword": "doc",
}


async def save_upload_file(file: UploadFile, user_id: str) -> tuple[str, int]:
    """Save uploaded file to disk, return (path, size)."""
    upload_dir = os.path.join(settings.UPLOAD_DIR, "resumes", user_id)
    os.makedirs(upload_dir, exist_ok=True)

    ext = os.path.splitext(file.filename or "")[1].lower() or ".pdf"
    unique_name = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(upload_dir, unique_name)

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds {settings.MAX_FILE_SIZE_MB}MB limit"
        )

    with open(file_path, "wb") as f:
        f.write(content)

    return file_path, len(content)


def get_file_type(file: UploadFile) -> str:
    """Determine file type from content type or filename."""
    if file.content_type in ALLOWED_TYPES:
        return ALLOWED_TYPES[file.content_type]
    name = (file.filename or "").lower()
    if name.endswith(".pdf"):
        return "pdf"
    if name.endswith(".docx"):
        return "docx"
    if name.endswith(".doc"):
        return "doc"
    raise HTTPException(
        status_code=400,
        detail="Only PDF and DOCX files are supported"
    )


def upload_resume(
    db: Session,
    user: User,
    file_path: str,
    file_name: str,
    file_type: str,
    file_size: int,
    version_name: Optional[str] = None,
) -> Resume:
    """Create resume record in DB."""
    # If this is first resume, make it primary
    existing_count = db.query(Resume).filter(Resume.user_id == user.id).count()
    is_primary = existing_count == 0

    resume = Resume(
        user_id=user.id,
        file_name=file_name,
        file_path=file_path,
        file_type=file_type,
        file_size=file_size,
        version_name=version_name or file_name,
        is_primary=is_primary,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


def parse_and_analyze_resume(db: Session, resume: Resume) -> Resume:
    """Extract text and use Groq to analyze resume."""
    try:
        # 1. Extract text
        text = extract_resume_text(resume.file_path, resume.file_type)
        resume.parsed_text = text

        # 2. Groq analysis
        try:
            extracted = analyze_resume(text)
            resume.extracted_data = extracted
            resume.quality_score = extracted.get("quality_score", 0)
            resume.is_analyzed = True
        except Exception as ai_err:
            logger.error(f"Groq analysis failed for resume {resume.id}: {ai_err}")
            # Still save the text, just without AI analysis
            resume.is_analyzed = False

        db.commit()
        db.refresh(resume)
        return resume

    except Exception as e:
        logger.error(f"Resume parsing failed for {resume.id}: {e}")
        raise HTTPException(
            status_code=422,
            detail=f"Could not process resume: {str(e)}"
        )


def set_primary_resume(db: Session, resume_id: str, user_id: str) -> Resume:
    """Set a resume as the primary/default."""
    # Unset all others
    db.query(Resume).filter(
        Resume.user_id == user_id,
        Resume.id != resume_id
    ).update({"is_primary": False})

    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == user_id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    resume.is_primary = True
    db.commit()
    db.refresh(resume)
    return resume


def delete_resume(db: Session, resume_id: str, user_id: str) -> None:
    """Delete resume record and file."""
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == user_id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    # Delete file
    if resume.file_path and os.path.exists(resume.file_path):
        try:
            os.remove(resume.file_path)
        except OSError as e:
            logger.warning(f"Could not delete file {resume.file_path}: {e}")

    db.delete(resume)
    db.commit()
