from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.job import Job, JobMatch, SavedJob
from app.models.resume import Resume
from app.services.jobs.discovery_service import run_job_discovery, get_jobs_paginated
from app.services.ai.groq_client import analyze_job_description, calculate_job_match, extract_candidate_profile

router = APIRouter(prefix="/jobs", tags=["Jobs"])


def job_to_dict(job: Job) -> dict:
    return {
        "id": job.id,
        "title": job.title,
        "company": job.company,
        "company_logo": job.company_logo,
        "location": job.location,
        "country": job.country,
        "city": job.city,
        "is_remote": job.is_remote,
        "is_hybrid": job.is_hybrid,
        "employment_type": job.employment_type,
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "salary_currency": job.salary_currency,
        "experience_min": job.experience_min,
        "experience_max": job.experience_max,
        "description": job.description,
        "requirements": job.requirements or [],
        "skills_required": job.skills_required or [],
        "skills_preferred": job.skills_preferred or [],
        "apply_url": job.apply_url,
        "source": job.source,
        "posted_at": job.posted_at.isoformat() if job.posted_at else None,
        "deadline": job.deadline.isoformat() if job.deadline else None,
        "industry": job.industry,
        "is_active": job.is_active,
        "created_at": job.created_at.isoformat() if job.created_at else None,
    }


def match_to_dict(match: JobMatch) -> dict:
    return {
        "id": match.id,
        "job_id": match.job_id,
        "match_score": match.match_score,
        "skills_match": match.skills_match,
        "experience_match": match.experience_match,
        "responsibility_match": match.responsibility_match,
        "education_match": match.education_match,
        "industry_match": match.industry_match,
        "location_match": match.location_match,
        "matching_skills": match.matching_skills or [],
        "missing_skills": match.missing_skills or [],
        "experience_alignment": match.experience_alignment,
        "qualification_alignment": match.qualification_alignment,
        "concerns": match.concerns or [],
        "reasons_to_apply": match.reasons_to_apply or [],
        "ai_recommendation": match.ai_recommendation,
        "match_category": match.match_category,
        "created_at": match.created_at.isoformat() if match.created_at else None,
    }


@router.get("")
def list_jobs(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: str = Query(""),
    location: str = Query(""),
    employment_type: str = Query(""),
    work_mode: str = Query(""),
    source: str = Query(""),
    sort: str = Query("-posted_at"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = get_jobs_paginated(
        db=db, page=page, per_page=per_page,
        search=search, location=location,
        employment_type=employment_type, work_mode=work_mode,
        source=source, sort=sort,
    )
    return {
        "items": [job_to_dict(j) for j in result["items"]],
        "total": result["total"],
        "page": result["page"],
        "per_page": result["per_page"],
        "total_pages": result["total_pages"],
    }


@router.get("/saved")
def get_saved_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    saved = (
        db.query(SavedJob)
        .filter(SavedJob.user_id == current_user.id)
        .order_by(SavedJob.created_at.desc())
        .all()
    )
    return {
        "items": [
            {
                "id": s.id,
                "status": s.status,
                "notes": s.notes,
                "job": job_to_dict(s.job) if s.job else None,
                "created_at": s.created_at.isoformat(),
            }
            for s in saved
        ],
        "total": len(saved),
    }


@router.get("/matches")
def get_job_matches(
    min_score: float = Query(0),
    category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = (
        db.query(JobMatch)
        .filter(JobMatch.user_id == current_user.id, JobMatch.match_score >= min_score)
        .order_by(JobMatch.match_score.desc())
    )
    if category:
        query = query.filter(JobMatch.match_category == category)

    total = query.count()
    matches = query.offset((page - 1) * per_page).limit(per_page).all()

    return {
        "items": [
            {**match_to_dict(m), "job": job_to_dict(m.job) if m.job else None}
            for m in matches
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.get("/{job_id}")
def get_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job_to_dict(job)


@router.post("/{job_id}/save")
def save_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    existing = db.query(SavedJob).filter(
        SavedJob.user_id == current_user.id,
        SavedJob.job_id == job_id,
    ).first()
    if existing:
        return {"message": "Job already saved", "id": existing.id}

    saved = SavedJob(user_id=current_user.id, job_id=job_id)
    db.add(saved)
    db.commit()
    return {"message": "Job saved successfully", "id": saved.id}


@router.delete("/{job_id}/save")
def unsave_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    saved = db.query(SavedJob).filter(
        SavedJob.user_id == current_user.id,
        SavedJob.job_id == job_id,
    ).first()
    if saved:
        db.delete(saved)
        db.commit()
    return {"message": "Job removed from saved"}


@router.post("/{job_id}/match")
def match_job(
    job_id: str,
    resume_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Get resume
    if resume_id:
        resume = db.query(Resume).filter(
            Resume.id == resume_id, Resume.user_id == current_user.id
        ).first()
    else:
        resume = db.query(Resume).filter(
            Resume.user_id == current_user.id, Resume.is_primary == True
        ).first()

    if not resume or not resume.extracted_data:
        raise HTTPException(
            status_code=422,
            detail="Please upload and analyze your resume first before matching jobs."
        )

    # Build candidate profile
    from app.models.user import UserProfile
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    profile_dict = {}
    if profile:
        profile_dict = {
            "name": current_user.full_name,
            "current_title": profile.current_title,
            "total_experience_years": profile.total_experience_years,
            "technical_skills": profile.technical_skills,
            "soft_skills": profile.soft_skills,
            "industries": profile.industries,
        }

    candidate = {**resume.extracted_data, **profile_dict}

    # Analyze job
    try:
        job_analysis = analyze_job_description(job.description, job.title, job.company)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")

    # Calculate match
    try:
        match_data = calculate_job_match(candidate, job_analysis, job_to_dict(job))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI matching error: {str(e)}")

    # Upsert match record
    existing_match = db.query(JobMatch).filter(
        JobMatch.user_id == current_user.id,
        JobMatch.job_id == job_id,
    ).first()

    if existing_match:
        for key, val in match_data.items():
            if hasattr(existing_match, key):
                setattr(existing_match, key, val)
        db.commit()
        db.refresh(existing_match)
        return {**match_to_dict(existing_match), "job": job_to_dict(job)}

    match = JobMatch(
        user_id=current_user.id,
        job_id=job_id,
        resume_id=resume.id,
        match_score=match_data.get("overall_score", 0),
        skills_match=match_data.get("skills_match", 0),
        experience_match=match_data.get("experience_match", 0),
        responsibility_match=match_data.get("responsibility_match", 0),
        education_match=match_data.get("education_match", 0),
        industry_match=match_data.get("industry_match", 0),
        location_match=match_data.get("location_match", 0),
        matching_skills=match_data.get("matching_skills", []),
        missing_skills=match_data.get("missing_skills", []),
        experience_alignment=match_data.get("experience_alignment"),
        qualification_alignment=match_data.get("qualification_alignment"),
        concerns=match_data.get("concerns", []),
        reasons_to_apply=match_data.get("reasons_to_apply", []),
        ai_recommendation=match_data.get("ai_recommendation"),
        match_category=match_data.get("match_category", "low"),
    )
    db.add(match)
    db.commit()
    db.refresh(match)
    return {**match_to_dict(match), "job": job_to_dict(job)}


@router.post("/discover")
def trigger_discovery(
    background_tasks: BackgroundTasks,
    keywords: Optional[List[str]] = None,
    location: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Trigger background job discovery from ALL sources (LinkedIn, Indeed, Glassdoor, Google, Naukri, company ATS...)."""
    background_tasks.add_task(
        run_job_discovery,
        db=db,
        user=current_user,
        keywords=keywords,
        location=location,
    )
    return {
        "message": "Job discovery started from all sources. New jobs will appear shortly.",
        "sources": ["LinkedIn", "Indeed", "Glassdoor", "Google Jobs", "ZipRecruiter",
                     "Naukri", "Greenhouse", "Lever", "Ashby", "Wellfound",
                     "WeWorkRemotely", "Remotive", "Adzuna", "JSearch"],
    }


class TargetedSearchRequest(BaseModel):
    company_websites: List[str]
    keywords: Optional[List[str]] = None


@router.post("/discover/companies")
def targeted_company_search(
    payload: TargetedSearchRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Crawl specific company career pages for their job postings."""
    from app.services.jobs.discovery_service import run_targeted_company_search

    def run():
        run_targeted_company_search(
            db=db, user=current_user,
            company_websites=payload.company_websites,
            keywords=payload.keywords,
        )

    background_tasks.add_task(run)
    return {
        "message": f"Crawling {len(payload.company_websites)} company career pages...",
        "companies": payload.company_websites,
    }


@router.post("/discover/company/{company_name}")
def crawl_single_company(
    company_name: str,
    website: str = Query(...),
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Crawl a single company's career page for job listings."""
    from app.integrations.job_sources.career_crawler import CareerPageCrawler
    from app.services.jobs.discovery_service import (
        build_search_keywords, compute_job_fingerprint, listing_to_job
    )
    from app.models.user import JobPreferences

    preferences = db.query(JobPreferences).filter(
        JobPreferences.user_id == current_user.id
    ).first()
    keywords = build_search_keywords(preferences)

    crawler = CareerPageCrawler(company_name=company_name, website=website)
    listings = crawler.crawl_company(website, company_name, keywords, limit=30)

    new_jobs = 0
    existing_fps = {j.external_id for j in db.query(Job.external_id).all()}
    for listing in listings:
        if not listing.title or not listing.apply_url:
            continue
        fp = compute_job_fingerprint(listing)
        if fp in existing_fps:
            continue
        existing_fps.add(fp)
        db.add(listing_to_job(listing, fp))
        new_jobs += 1
    db.commit()

    return {
        "company": company_name,
        "jobs_found": len(listings),
        "new_jobs_saved": new_jobs,
        "jobs": [
            {"title": j.title, "apply_url": j.apply_url, "location": j.location}
            for j in listings[:20]
        ],
    }
