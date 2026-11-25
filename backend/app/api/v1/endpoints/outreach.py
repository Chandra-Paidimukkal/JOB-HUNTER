from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.outreach import OutreachContact, GeneratedEmail, LinkedInMessage

router = APIRouter(prefix="/outreach", tags=["Outreach"])

VALID_STATUSES = [
    "new_prospect", "research_completed", "email_generated",
    "ready_to_send", "sent", "follow_up_due", "response_received",
    "interested", "not_interested",
]


class CreateOutreachRequest(BaseModel):
    company_name: str
    company_website: Optional[str] = None
    company_industry: Optional[str] = None
    contact_name: Optional[str] = None
    contact_designation: Optional[str] = None
    contact_email: Optional[str] = None
    contact_linkedin: Optional[str] = None
    department: Optional[str] = None
    email_type: Optional[str] = None
    email_subject: Optional[str] = None
    generated_email: Optional[str] = None
    notes: Optional[str] = None


class UpdateOutreachRequest(BaseModel):
    status: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    email_subject: Optional[str] = None
    generated_email: Optional[str] = None
    sent_date: Optional[datetime] = None
    follow_up_date: Optional[datetime] = None
    response_received: Optional[bool] = None
    response_notes: Optional[str] = None
    notes: Optional[str] = None


class SaveGeneratedEmailRequest(BaseModel):
    outreach_contact_id: Optional[str] = None
    email_type: str
    subject_lines: List[str]
    selected_subject: Optional[str] = None
    short_version: Optional[str] = None
    medium_version: Optional[str] = None
    detailed_version: Optional[str] = None
    selected_version: Optional[str] = None
    tone: Optional[str] = None
    reasoning: Optional[str] = None
    suggestions: Optional[List[str]] = None


def contact_to_dict(c: OutreachContact) -> dict:
    return {
        "id": c.id,
        "company_name": c.company_name,
        "company_website": c.company_website,
        "company_industry": c.company_industry,
        "contact_name": c.contact_name,
        "contact_designation": c.contact_designation,
        "contact_email": c.contact_email,
        "contact_linkedin": c.contact_linkedin,
        "department": c.department,
        "status": c.status,
        "email_type": c.email_type,
        "email_subject": c.email_subject,
        "generated_email": c.generated_email,
        "sent_date": c.sent_date.isoformat() if c.sent_date else None,
        "follow_up_date": c.follow_up_date.isoformat() if c.follow_up_date else None,
        "response_received": c.response_received,
        "response_notes": c.response_notes,
        "notes": c.notes,
        "created_at": c.created_at.isoformat(),
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }


@router.get("")
def list_outreach(
    status: Optional[str] = Query(None),
    search: str = Query(""),
    page: int = Query(1, ge=1),
    per_page: int = Query(20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(OutreachContact).filter(OutreachContact.user_id == current_user.id)
    if status:
        query = query.filter(OutreachContact.status == status)
    if search:
        query = query.filter(
            OutreachContact.company_name.ilike(f"%{search}%") |
            OutreachContact.contact_name.ilike(f"%{search}%")
        )
    query = query.order_by(OutreachContact.created_at.desc())
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return {
        "items": [contact_to_dict(c) for c in items],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.post("", status_code=201)
def create_outreach(
    payload: CreateOutreachRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contact = OutreachContact(user_id=current_user.id, **payload.model_dump())
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact_to_dict(contact)


@router.get("/{contact_id}")
def get_outreach(
    contact_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contact = db.query(OutreachContact).filter(
        OutreachContact.id == contact_id,
        OutreachContact.user_id == current_user.id
    ).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Outreach contact not found")
    return contact_to_dict(contact)


@router.put("/{contact_id}")
def update_outreach(
    contact_id: str,
    payload: UpdateOutreachRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contact = db.query(OutreachContact).filter(
        OutreachContact.id == contact_id,
        OutreachContact.user_id == current_user.id
    ).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Outreach contact not found")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(contact, field, value)

    db.commit()
    db.refresh(contact)
    return contact_to_dict(contact)


@router.delete("/{contact_id}", status_code=204)
def delete_outreach(
    contact_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contact = db.query(OutreachContact).filter(
        OutreachContact.id == contact_id,
        OutreachContact.user_id == current_user.id
    ).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(contact)
    db.commit()


@router.post("/emails/save")
def save_generated_email(
    payload: SaveGeneratedEmailRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    email = GeneratedEmail(user_id=current_user.id, **payload.model_dump())
    db.add(email)
    db.commit()
    db.refresh(email)
    return {"id": email.id, "message": "Email saved"}


@router.post("/linkedin/save")
def save_linkedin_message(
    recipient_name: Optional[str] = None,
    recipient_title: Optional[str] = None,
    company_name: Optional[str] = None,
    message_type: str = "connection",
    generated_message: str = "",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    msg = LinkedInMessage(
        user_id=current_user.id,
        recipient_name=recipient_name,
        recipient_title=recipient_title,
        company_name=company_name,
        message_type=message_type,
        generated_message=generated_message,
        character_count=len(generated_message),
    )
    db.add(msg)
    db.commit()
    return {"id": msg.id, "message": "LinkedIn message saved"}
