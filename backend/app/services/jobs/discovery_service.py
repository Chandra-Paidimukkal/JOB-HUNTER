"""
Job Discovery Service — orchestrates all job source connectors,
deduplicates listings, and stores them in the database.
"""
import logging
import hashlib
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.job import Job, JobSkill
from app.models.user import User, JobPreferences
from app.integrations.job_sources.base import JobListing
from app.integrations.job_sources.adzuna import AdzunaConnector
from app.integrations.job_sources.remotive import RemotiveConnector
from app.integrations.job_sources.jsearch import JSearchConnector

logger = logging.getLogger(__name__)

# All registered connectors
ALL_CONNECTORS = [
    AdzunaConnector(),
    RemotiveConnector(),
    JSearchConnector(),
]


def build_search_keywords(preferences: JobPreferences) -> List[str]:
    """Build search keywords from user preferences."""
    keywords = []
    if preferences.preferred_titles:
        keywords.extend(preferences.preferred_titles[:3])
    return keywords or ["software engineer"]


def compute_job_fingerprint(listing: JobListing) -> str:
    """Create a deduplication hash from title + company + location."""
    text = f"{listing.title.lower().strip()}{listing.company.lower().strip()}{listing.apply_url.lower().strip()}"
    return hashlib.md5(text.encode()).hexdigest()


def listing_to_job(listing: JobListing, fingerprint: str) -> Job:
    """Convert a JobListing dataclass to a Job ORM model."""
    return Job(
        title=listing.title[:255],
        company=listing.company[:255],
        company_logo=listing.company_logo,
        location=(listing.location or "")[:255],
        country=listing.country,
        city=listing.city,
        is_remote=listing.is_remote,
        is_hybrid=listing.is_hybrid,
        employment_type=listing.employment_type,
        salary_min=listing.salary_min,
        salary_max=listing.salary_max,
        salary_currency=listing.salary_currency,
        experience_min=listing.experience_min,
        experience_max=listing.experience_max,
        description=listing.description,
        requirements=listing.requirements,
        skills_required=listing.skills_required,
        skills_preferred=listing.skills_preferred,
        apply_url=listing.apply_url,
        source=listing.source,
        external_id=fingerprint,
        posted_at=listing.posted_at,
        deadline=listing.deadline,
        industry=listing.industry,
        is_active=True,
    )


def run_job_discovery(
    db: Session,
    user: User,
    keywords: Optional[List[str]] = None,
    location: Optional[str] = None,
    remote_only: bool = False,
    limit_per_source: int = 30,
) -> Dict:
    """
    Main discovery function.
    Searches all configured sources, deduplicates, and saves to DB.
    """
    preferences = db.query(JobPreferences).filter(
        JobPreferences.user_id == user.id
    ).first()

    if keywords is None:
        keywords = build_search_keywords(preferences) if preferences else ["software engineer"]

    if location is None and preferences:
        cities = preferences.preferred_cities
        location = cities[0] if cities else None

    if remote_only is False and preferences:
        remote_only = preferences.remote_ok and not preferences.onsite_ok

    all_listings: List[JobListing] = []
    source_results = {}

    for connector in ALL_CONNECTORS:
        status = connector.get_status()
        if not status["configured"]:
            source_results[connector.name] = {
                "status": "not_configured",
                "count": 0,
                "message": f"{connector.name} requires API credentials. Configure in Settings → Integrations.",
            }
            continue

        try:
            listings = connector.search(
                keywords=keywords,
                location=location,
                remote_only=remote_only,
                limit=limit_per_source,
            )
            all_listings.extend(listings)
            source_results[connector.name] = {"status": "success", "count": len(listings)}
            logger.info(f"{connector.name}: fetched {len(listings)} listings")
        except Exception as e:
            logger.error(f"{connector.name} search failed: {e}")
            source_results[connector.name] = {"status": "error", "count": 0, "message": str(e)}

    # Deduplication
    seen_fingerprints = set()
    new_jobs = 0
    duplicate_jobs = 0

    for listing in all_listings:
        fp = compute_job_fingerprint(listing)
        if fp in seen_fingerprints:
            duplicate_jobs += 1
            continue
        seen_fingerprints.add(fp)

        # Check if already in DB
        existing = db.query(Job).filter(Job.external_id == fp).first()
        if existing:
            duplicate_jobs += 1
            continue

        # Save new job
        job = listing_to_job(listing, fp)
        db.add(job)
        db.flush()

        # Save skills
        for skill in listing.skills_required[:20]:
            db.add(JobSkill(job_id=job.id, skill_name=skill[:255], is_required=True))
        for skill in listing.skills_preferred[:10]:
            db.add(JobSkill(job_id=job.id, skill_name=skill[:255], is_required=False))

        new_jobs += 1

    db.commit()

    return {
        "total_fetched": len(all_listings),
        "new_jobs_saved": new_jobs,
        "duplicates_skipped": duplicate_jobs,
        "sources": source_results,
        "keywords_used": keywords,
    }


def get_jobs_paginated(
    db: Session,
    page: int = 1,
    per_page: int = 20,
    search: str = "",
    location: str = "",
    employment_type: str = "",
    work_mode: str = "",
    source: str = "",
    sort: str = "-posted_at",
    is_active: bool = True,
) -> Dict:
    """Paginated job listing with filters."""
    query = db.query(Job).filter(Job.is_active == is_active)

    if search:
        query = query.filter(
            Job.title.ilike(f"%{search}%") |
            Job.company.ilike(f"%{search}%") |
            Job.description.ilike(f"%{search}%")
        )
    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))
    if employment_type:
        query = query.filter(Job.employment_type.ilike(f"%{employment_type}%"))
    if source:
        query = query.filter(Job.source == source)
    if work_mode == "remote":
        query = query.filter(Job.is_remote == True)
    elif work_mode == "hybrid":
        query = query.filter(Job.is_hybrid == True)
    elif work_mode == "onsite":
        query = query.filter(Job.is_remote == False, Job.is_hybrid == False)

    # Sorting
    sort_map = {
        "-posted_at": Job.posted_at.desc(),
        "posted_at": Job.posted_at.asc(),
        "-salary_max": Job.salary_max.desc(),
        "salary_max": Job.salary_max.asc(),
        "title": Job.title.asc(),
        "company": Job.company.asc(),
    }
    query = query.order_by(sort_map.get(sort, Job.created_at.desc()))

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": max(1, -(-total // per_page)),
    }
