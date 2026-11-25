from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User, UserProfile, JobPreferences

router = APIRouter(prefix="/profile", tags=["Profile"])


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    current_location: Optional[str] = None
    preferred_locations: Optional[List[str]] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    website_url: Optional[str] = None
    current_title: Optional[str] = None
    current_company: Optional[str] = None
    total_experience_years: Optional[float] = None
    professional_summary: Optional[str] = None
    technical_skills: Optional[List[str]] = None
    soft_skills: Optional[List[str]] = None
    industries: Optional[List[str]] = None
    notice_period: Optional[str] = None
    willing_to_relocate: Optional[bool] = None


class PreferencesUpdate(BaseModel):
    preferred_titles: Optional[List[str]] = None
    preferred_industries: Optional[List[str]] = None
    preferred_companies: Optional[List[str]] = None
    preferred_countries: Optional[List[str]] = None
    preferred_cities: Optional[List[str]] = None
    remote_ok: Optional[bool] = None
    hybrid_ok: Optional[bool] = None
    onsite_ok: Optional[bool] = None
    full_time: Optional[bool] = None
    part_time: Optional[bool] = None
    contract: Optional[bool] = None
    internship: Optional[bool] = None
    expected_salary: Optional[float] = None
    min_salary: Optional[float] = None
    currency: Optional[str] = None
    career_objective: Optional[str] = None
    short_term_goals: Optional[str] = None
    long_term_goals: Optional[str] = None
    desired_responsibilities: Optional[str] = None


class OnboardingPayload(BaseModel):
    personal: Optional[dict] = None
    professional: Optional[dict] = None
    preferences: Optional[dict] = None
    objective: Optional[dict] = None


@router.get("")
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    prefs = db.query(JobPreferences).filter(JobPreferences.user_id == current_user.id).first()
    return {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "avatar_url": current_user.avatar_url,
            "is_verified": current_user.is_verified,
            "onboarding_completed": current_user.onboarding_completed,
        },
        "profile": _profile_to_dict(profile) if profile else None,
        "preferences": _prefs_to_dict(prefs) if prefs else None,
    }


@router.put("")
def update_profile(
    payload: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.full_name:
        current_user.full_name = payload.full_name

    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)

    for field, value in payload.model_dump(exclude_none=True, exclude={"full_name"}).items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(current_user)
    return {"message": "Profile updated successfully", "profile": _profile_to_dict(profile)}


@router.get("/preferences")
def get_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    prefs = db.query(JobPreferences).filter(JobPreferences.user_id == current_user.id).first()
    return _prefs_to_dict(prefs) if prefs else {}


@router.put("/preferences")
def update_preferences(
    payload: PreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    prefs = db.query(JobPreferences).filter(JobPreferences.user_id == current_user.id).first()
    if not prefs:
        prefs = JobPreferences(user_id=current_user.id)
        db.add(prefs)

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(prefs, field, value)

    db.commit()
    return {"message": "Preferences updated successfully"}


@router.post("/onboarding")
def complete_onboarding(
    payload: OnboardingPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Update user full name
    personal = payload.personal or {}
    if personal.get("full_name"):
        current_user.full_name = personal["full_name"]

    # Upsert profile
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)

    p = payload.professional or {}
    profile.phone = personal.get("phone")
    profile.current_location = personal.get("current_location")
    profile.preferred_locations = [
        x.strip() for x in personal.get("preferred_locations", "").split(",") if x.strip()
    ] if isinstance(personal.get("preferred_locations"), str) else personal.get("preferred_locations", [])
    profile.linkedin_url = personal.get("linkedin_url")
    profile.portfolio_url = personal.get("portfolio_url")
    profile.website_url = personal.get("website_url")
    profile.current_title = p.get("current_title")
    profile.current_company = p.get("current_company")
    profile.total_experience_years = p.get("total_experience_years")
    profile.professional_summary = p.get("professional_summary")
    profile.technical_skills = p.get("technical_skills", [])
    profile.soft_skills = p.get("soft_skills", [])
    profile.industries = p.get("industries", [])

    # Upsert preferences
    prefs = db.query(JobPreferences).filter(JobPreferences.user_id == current_user.id).first()
    if not prefs:
        prefs = JobPreferences(user_id=current_user.id)
        db.add(prefs)

    pr = payload.preferences or {}
    for key, val in pr.items():
        if hasattr(prefs, key) and val is not None:
            setattr(prefs, key, val)

    # Objective
    obj = payload.objective or {}
    if prefs:
        prefs.career_objective = obj.get("career_objective")
        prefs.short_term_goals = obj.get("short_term_goals")
        prefs.long_term_goals = obj.get("long_term_goals")
        prefs.desired_responsibilities = obj.get("desired_responsibilities")

    current_user.onboarding_completed = True
    db.commit()
    return {"message": "Onboarding completed successfully"}


def _profile_to_dict(profile: UserProfile) -> dict:
    if not profile:
        return {}
    return {
        "id": profile.id,
        "phone": profile.phone,
        "current_location": profile.current_location,
        "preferred_locations": profile.preferred_locations or [],
        "linkedin_url": profile.linkedin_url,
        "portfolio_url": profile.portfolio_url,
        "website_url": profile.website_url,
        "current_title": profile.current_title,
        "current_company": profile.current_company,
        "total_experience_years": profile.total_experience_years,
        "professional_summary": profile.professional_summary,
        "technical_skills": profile.technical_skills or [],
        "soft_skills": profile.soft_skills or [],
        "industries": profile.industries or [],
        "notice_period": profile.notice_period,
        "willing_to_relocate": profile.willing_to_relocate,
        "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
    }


def _prefs_to_dict(prefs: JobPreferences) -> dict:
    if not prefs:
        return {}
    return {
        "id": prefs.id,
        "preferred_titles": prefs.preferred_titles or [],
        "preferred_industries": prefs.preferred_industries or [],
        "preferred_companies": prefs.preferred_companies or [],
        "preferred_countries": prefs.preferred_countries or [],
        "preferred_cities": prefs.preferred_cities or [],
        "remote_ok": prefs.remote_ok,
        "hybrid_ok": prefs.hybrid_ok,
        "onsite_ok": prefs.onsite_ok,
        "full_time": prefs.full_time,
        "part_time": prefs.part_time,
        "contract": prefs.contract,
        "internship": prefs.internship,
        "expected_salary": prefs.expected_salary,
        "min_salary": prefs.min_salary,
        "currency": prefs.currency,
        "career_objective": prefs.career_objective,
        "short_term_goals": prefs.short_term_goals,
        "long_term_goals": prefs.long_term_goals,
        "updated_at": prefs.updated_at.isoformat() if prefs.updated_at else None,
    }
