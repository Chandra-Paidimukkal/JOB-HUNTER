from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List
import os

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.resume import Resume
from app.services.resumes.resume_service import (
    save_upload_file, get_file_type, upload_resume,
    parse_and_analyze_resume, set_primary_resume, delete_resume
)

router = APIRouter(prefix="/resumes", tags=["Resumes"])


def resume_to_dict(r: Resume) -> dict:
    return {
        "id": r.id,
        "file_name": r.file_name,
        "file_type": r.file_type,
        "file_size": r.file_size,
        "version_name": r.version_name,
        "is_primary": r.is_primary,
        "is_analyzed": r.is_analyzed,
        "quality_score": r.quality_score,
        "extracted_data": r.extracted_data,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    }


@router.post("/upload", status_code=201)
async def upload_resume_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    version_name: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    file_type = get_file_type(file)
    file_path, file_size = await save_upload_file(file, current_user.id)

    resume = upload_resume(
        db=db,
        user=current_user,
        file_path=file_path,
        file_name=file.filename or "resume",
        file_type=file_type,
        file_size=file_size,
        version_name=version_name,
    )

    # Parse in background
    background_tasks.add_task(parse_and_analyze_resume, db, resume)

    return {
        "message": "Resume uploaded successfully. AI analysis is running in the background.",
        "resume": resume_to_dict(resume),
    }


@router.get("")
def list_resumes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resumes = (
        db.query(Resume)
        .filter(Resume.user_id == current_user.id)
        .order_by(Resume.is_primary.desc(), Resume.created_at.desc())
        .all()
    )
    return {"items": [resume_to_dict(r) for r in resumes], "total": len(resumes)}


@router.get("/{resume_id}")
def get_resume(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume_to_dict(resume)


@router.delete("/{resume_id}", status_code=204)
def delete_resume_endpoint(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    delete_resume(db, resume_id, current_user.id)


@router.put("/{resume_id}/primary")
def set_primary(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resume = set_primary_resume(db, resume_id, current_user.id)
    return {"message": "Primary resume updated", "resume": resume_to_dict(resume)}


@router.post("/{resume_id}/analyze")
def analyze_resume_endpoint(
    resume_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    if not resume.parsed_text:
        raise HTTPException(status_code=422, detail="Resume file could not be read")

    background_tasks.add_task(parse_and_analyze_resume, db, resume)
    return {"message": "Analysis started. Refresh in a few seconds to see results."}
