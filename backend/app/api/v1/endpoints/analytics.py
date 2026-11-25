from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy import func

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.application import Application
from app.models.job import Job, JobMatch, SavedJob
from app.models.outreach import OutreachContact, SentEmail, GeneratedEmail

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview")
def get_overview(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    uid = current_user.id

    total_jobs = db.query(Job).count()
    high_match = db.query(JobMatch).filter(
        JobMatch.user_id == uid,
        JobMatch.match_score >= 70,
    ).count()
    saved_jobs = db.query(SavedJob).filter(SavedJob.user_id == uid).count()

    apps_query = db.query(Application).filter(Application.user_id == uid)
    total_apps = apps_query.count()
    submitted = apps_query.filter(Application.status == "applied").count()
    interviews = apps_query.filter(Application.status.in_(
        ["interview_scheduled", "interview_completed"]
    )).count()
    offers = apps_query.filter(Application.status == "offer_received").count()
    rejections = apps_query.filter(Application.status == "rejected").count()

    emails_gen = db.query(GeneratedEmail).filter(GeneratedEmail.user_id == uid).count()
    emails_sent = db.query(SentEmail).filter(SentEmail.user_id == uid).count()
    responses = db.query(OutreachContact).filter(
        OutreachContact.user_id == uid,
        OutreachContact.response_received == True,
    ).count()

    return {
        "total_jobs_discovered": total_jobs,
        "relevant_jobs": high_match,
        "high_match_jobs": high_match,
        "saved_jobs": saved_jobs,
        "applications_prepared": total_apps,
        "applications_submitted": submitted,
        "emails_generated": emails_gen,
        "outreach_sent": emails_sent,
        "recruiter_responses": responses,
        "interviews_scheduled": interviews,
        "offers_received": offers,
        "rejections": rejections,
    }


@router.get("/applications")
def get_application_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    uid = current_user.id

    # Status breakdown
    status_counts = (
        db.query(Application.status, func.count(Application.id).label("count"))
        .filter(Application.user_id == uid)
        .group_by(Application.status)
        .all()
    )

    # Applications over time (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    daily_apps = (
        db.query(
            func.date(Application.created_at).label("date"),
            func.count(Application.id).label("count"),
        )
        .filter(Application.user_id == uid, Application.created_at >= thirty_days_ago)
        .group_by(func.date(Application.created_at))
        .order_by(func.date(Application.created_at))
        .all()
    )

    # Top companies applied to
    top_companies = (
        db.query(Job.company, func.count(Application.id).label("count"))
        .join(Application, Application.job_id == Job.id)
        .filter(Application.user_id == uid)
        .group_by(Job.company)
        .order_by(func.count(Application.id).desc())
        .limit(10)
        .all()
    )

    return {
        "status_breakdown": [{"status": s, "count": c} for s, c in status_counts],
        "daily_applications": [
            {"date": str(d), "count": c} for d, c in daily_apps
        ],
        "top_companies": [{"company": co, "count": c} for co, c in top_companies],
    }


@router.get("/outreach")
def get_outreach_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    uid = current_user.id

    total_contacts = db.query(OutreachContact).filter(OutreachContact.user_id == uid).count()
    sent = db.query(OutreachContact).filter(
        OutreachContact.user_id == uid,
        OutreachContact.status.in_(["sent", "follow_up_due", "response_received", "interested"]),
    ).count()
    responses = db.query(OutreachContact).filter(
        OutreachContact.user_id == uid,
        OutreachContact.response_received == True,
    ).count()

    response_rate = round((responses / sent * 100), 1) if sent > 0 else 0

    # By email type
    type_counts = (
        db.query(OutreachContact.email_type, func.count(OutreachContact.id).label("count"))
        .filter(OutreachContact.user_id == uid)
        .group_by(OutreachContact.email_type)
        .all()
    )

    return {
        "total_contacts": total_contacts,
        "emails_sent": sent,
        "responses_received": responses,
        "response_rate": response_rate,
        "by_email_type": [{"type": t or "unset", "count": c} for t, c in type_counts],
    }


@router.get("/job-matches")
def get_match_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    uid = current_user.id

    category_counts = (
        db.query(JobMatch.match_category, func.count(JobMatch.id).label("count"))
        .filter(JobMatch.user_id == uid)
        .group_by(JobMatch.match_category)
        .all()
    )

    avg_score = (
        db.query(func.avg(JobMatch.match_score))
        .filter(JobMatch.user_id == uid)
        .scalar()
    )

    return {
        "by_category": [{"category": cat, "count": c} for cat, c in category_counts],
        "average_match_score": round(float(avg_score or 0), 1),
        "total_matches": sum(c for _, c in category_counts),
    }
