"""
Gmail OAuth integration endpoints.
Uses Google's official OAuth 2.0 flow.
Requires GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET in .env
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import logging

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.config import settings
from app.models.user import User
from app.models.integration import UserIntegration
from app.models.outreach import SentEmail

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/email", tags=["Email Integration"])


class ConnectEmailRequest(BaseModel):
    code: str  # OAuth authorization code


class SendEmailRequest(BaseModel):
    to_email: str
    subject: str
    body: str
    outreach_contact_id: Optional[str] = None


class DraftEmailRequest(BaseModel):
    to_email: str
    subject: str
    body: str


def _get_integration(db: Session, user_id: str) -> Optional[UserIntegration]:
    return db.query(UserIntegration).filter(
        UserIntegration.user_id == user_id,
        UserIntegration.provider == "gmail",
        UserIntegration.is_active == True,
    ).first()


@router.get("/status")
def get_email_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    integration = _get_integration(db, current_user.id)
    if not settings.GMAIL_CLIENT_ID:
        return {
            "connected": False,
            "configured": False,
            "message": "Gmail integration requires GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET. Configure in .env",
        }
    return {
        "connected": integration is not None,
        "configured": True,
        "email": integration.email if integration else None,
        "connected_at": integration.connected_at.isoformat() if integration else None,
    }


@router.get("/auth-url")
def get_auth_url(current_user: User = Depends(get_current_user)):
    """Get Google OAuth URL for Gmail authorization."""
    if not settings.GMAIL_CLIENT_ID:
        raise HTTPException(
            status_code=503,
            detail="Gmail not configured. Set GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET in .env"
        )
    scopes = [
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.compose",
    ]
    scope_str = " ".join(scopes)
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={settings.GMAIL_CLIENT_ID}"
        f"&redirect_uri={settings.GMAIL_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope={scope_str}"
        f"&access_type=offline"
        f"&prompt=consent"
        f"&state={current_user.id}"
    )
    return {"auth_url": auth_url}


@router.post("/connect")
def connect_gmail(
    payload: ConnectEmailRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Exchange OAuth code for tokens and store."""
    if not settings.GMAIL_CLIENT_ID:
        raise HTTPException(status_code=503, detail="Gmail not configured")

    try:
        import requests
        token_response = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": payload.code,
                "client_id": settings.GMAIL_CLIENT_ID,
                "client_secret": settings.GMAIL_CLIENT_SECRET,
                "redirect_uri": settings.GMAIL_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
            timeout=15,
        )
        token_data = token_response.json()
        if "error" in token_data:
            raise HTTPException(status_code=400, detail=f"OAuth error: {token_data['error']}")

        # Get user email
        userinfo_response = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
            timeout=10,
        )
        userinfo = userinfo_response.json()

        # Upsert integration
        integration = _get_integration(db, current_user.id)
        if not integration:
            integration = UserIntegration(user_id=current_user.id, provider="gmail")
            db.add(integration)

        integration.access_token = token_data.get("access_token")
        integration.refresh_token = token_data.get("refresh_token")
        integration.email = userinfo.get("email")
        integration.scopes = ["gmail.send", "gmail.readonly", "gmail.compose"]
        integration.is_active = True
        if token_data.get("expires_in"):
            integration.token_expires_at = datetime.utcnow() + timedelta(
                seconds=token_data["expires_in"]
            )

        db.commit()
        return {"message": "Gmail connected successfully", "email": integration.email}

    except Exception as e:
        logger.error(f"Gmail OAuth error: {e}")
        raise HTTPException(status_code=400, detail=f"Gmail connection failed: {str(e)}")


@router.delete("/connect")
def disconnect_gmail(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    integration = _get_integration(db, current_user.id)
    if integration:
        integration.is_active = False
        db.commit()
    return {"message": "Gmail disconnected"}


@router.post("/draft")
def create_draft(
    payload: DraftEmailRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a Gmail draft."""
    integration = _get_integration(db, current_user.id)
    if not integration:
        raise HTTPException(status_code=403, detail="Gmail not connected. Connect Gmail first.")

    try:
        import base64
        from email.mime.text import MIMEText
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials

        creds = Credentials(token=integration.access_token)
        service = build("gmail", "v1", credentials=creds)

        message = MIMEText(payload.body, "plain")
        message["to"] = payload.to_email
        message["subject"] = payload.subject

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        draft = service.users().drafts().create(
            userId="me",
            body={"message": {"raw": raw}}
        ).execute()

        return {"message": "Draft created in Gmail", "draft_id": draft.get("id")}

    except Exception as e:
        logger.error(f"Gmail draft error: {e}")
        raise HTTPException(status_code=503, detail=f"Could not create draft: {str(e)}")


@router.post("/send")
def send_email(
    payload: SendEmailRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Send an email via Gmail.
    REQUIRES explicit user confirmation before calling this endpoint.
    The frontend must display the full email to the user before calling /send.
    """
    integration = _get_integration(db, current_user.id)
    if not integration:
        raise HTTPException(status_code=403, detail="Gmail not connected")

    try:
        import base64
        from email.mime.text import MIMEText
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials

        creds = Credentials(token=integration.access_token)
        service = build("gmail", "v1", credentials=creds)

        message = MIMEText(payload.body, "plain")
        message["to"] = payload.to_email
        message["subject"] = payload.subject

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        sent = service.users().messages().send(
            userId="me",
            body={"raw": raw}
        ).execute()

        # Record in DB
        sent_record = SentEmail(
            user_id=current_user.id,
            outreach_contact_id=payload.outreach_contact_id,
            to_email=payload.to_email,
            subject=payload.subject,
            body=payload.body,
            gmail_message_id=sent.get("id"),
            sent_via="gmail",
        )
        db.add(sent_record)
        db.commit()

        return {"message": "Email sent successfully", "gmail_id": sent.get("id")}

    except Exception as e:
        logger.error(f"Gmail send error: {e}")
        raise HTTPException(status_code=503, detail=f"Email send failed: {str(e)}")


@router.get("/history")
def get_email_history(
    page: int = 1,
    per_page: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    total = db.query(SentEmail).filter(SentEmail.user_id == current_user.id).count()
    items = (
        db.query(SentEmail)
        .filter(SentEmail.user_id == current_user.id)
        .order_by(SentEmail.sent_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return {
        "items": [
            {
                "id": e.id,
                "to_email": e.to_email,
                "subject": e.subject,
                "body": e.body,
                "sent_at": e.sent_at.isoformat(),
                "sent_via": e.sent_via,
            }
            for e in items
        ],
        "total": total,
        "page": page,
    }
