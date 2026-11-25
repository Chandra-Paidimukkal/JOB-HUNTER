from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.application import Application
from app.models.job import Job

router = APIRouter(prefix="/applications", tags=["Applications"])

VALID_STATUSES = [
    "saved", "recommended", "ready_to_apply", "applied", "under_review",
    "recruiter_contacted", "interview_scheduled", "interview_completed",
    "assessment_pending", "offer_received", "rejected", "withdrawn"
]


class CreateApplicationRequest(BaseModel):
    job_id: str
    status: str = "saved"
    resume_id: Optional[str] = None
    cover_letter: Optional[str] = None
    notes: Optional[str] = None
    match_score: Optional[float] = None


class UpdateApplicationRequest(BaseModel):
    status: Optional[str] = None
    cover_letter: Optional[str] = None
    recruiter_name: Optional[str] = None
    recruiter_email: Optional[str] = None
    recruiter_linkedin: Optional[str] = None
    follow_up_date: Optional[datetime] = None
    applied_date: Optional[datetime] = None
    notes: Optional[str] = None


def app_to_dict(app: Application) -> dict:
    return {
        "id": app.id,
        "job_id": app.job_id,
        "status": app.status,
        "applied_date": app.applied_date.isoformat() if app.applied_date else None,
        "cover_letter": app.cover_letter,
        "recruiter_name": app.recruiter_name,
        "recruiter_email": app.recruiter_email,
        "recruiter_linkedin": app.recruiter_linkedin,
        "follow_up_date": app.follow_up_date.isoformat() if app.follow_up_date else None,
        "notes": app.notes,
        "match_score": app.match_score,
        "job": {
            "id": app.job.id,
            "title": app.job.title,
            "company": app.job.company,
            "company_logo": app.job.company_logo,
            "location": app.job.location,
            "is_remote": app.job.is_remote,
            "employment_type": app.job.employment_type,
            "salary_min": app.job.salary_min,
            "salary_max": app.job.salary_max,
            "apply_url": app.job.apply_url,
            "source": app.job.source,
        } if app.job else None,
        "created_at": app.created_at.isoformat(),
        "updated_at": app.updated_at.isoformat() if app.updated_at else None,
    }


@router.get("")
def list_applications(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    sort: str = Query("-created_at"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Application).filter(Application.user_id == current_user.id)
    if status:
        query = query.filter(Application.status == status)

    sort_map = {
        "-created_at": Application.created_at.desc(),
        "created_at": Application.created_at.asc(),
        "-applied_date": Application.applied_date.desc(),
        "status": Application.status.asc(),
    }
    query = query.order_by(sort_map.get(sort, Application.created_at.desc()))

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()

    return {
        "items": [app_to_dict(a) for a in items],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": max(1, -(-total // per_page)),
    }


@router.post("", status_code=201)
def create_application(
    payload: CreateApplicationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status: {payload.status}")

    job = db.query(Job).filter(Job.id == payload.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Check for duplicate
    existing = db.query(Application).filter(
        Application.user_id == current_user.id,
        Application.job_id == payload.job_id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Application already exists for this job")

    app = Application(
        user_id=current_user.id,
        job_id=payload.job_id,
        status=payload.status,
        resume_id=payload.resume_id,
        cover_letter=payload.cover_letter,
        notes=payload.notes,
        match_score=payload.match_score,
        applied_date=datetime.utcnow() if payload.status == "applied" else None,
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return app_to_dict(app)


@router.get("/{app_id}")
def get_application(
    app_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    app = db.query(Application).filter(
        Application.id == app_id,
        Application.user_id == current_user.id
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app_to_dict(app)


@router.put("/{app_id}")
def update_application(
    app_id: str,
    payload: UpdateApplicationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    app = db.query(Application).filter(
        Application.id == app_id,
        Application.user_id == current_user.id
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    if payload.status and payload.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status: {payload.status}")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(app, field, value)

    if payload.status == "applied" and not app.applied_date:
        app.applied_date = datetime.utcnow()

    db.commit()
    db.refresh(app)
    return app_to_dict(app)


@router.delete("/{app_id}", status_code=204)
def delete_application(
    app_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    app = db.query(Application).filter(
        Application.id == app_id,
        Application.user_id == current_user.id
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    db.delete(app)
    db.commit()
