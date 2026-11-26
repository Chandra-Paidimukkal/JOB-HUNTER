"""
Job Discovery Service — orchestrates ALL job source connectors in parallel.
Sources: LinkedIn, Indeed, Glassdoor, Google Jobs, ZipRecruiter, Naukri,
Greenhouse, Lever, Ashby, Wellfound, WeWorkRemotely, Remotive, Adzuna, JSearch.
"""
import logging
import hashlib
import concurrent.futures
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.job import Job, JobSkill
from app.models.user import User, JobPreferences
from app.integrations.job_sources.base import JobListing
from app.integrations.job_sources.adzuna import AdzunaConnector
from app.integrations.job_sources.remotive import RemotiveConnector
from app.integrations.job_sources.jsearch import JSearchConnector
from app.integrations.job_sources.jobspy_connector import JobSpyConnector
from app.integrations.job_sources.greenhouse_connector import GreenhouseConnector
from app.integrations.job_sources.lever_connector import LeverConnector
from app.integrations.job_sources.wellfound_connector import WellfoundConnector
from app.integrations.job_sources.weworkremotely_connector import WeWorkRemotelyConnector
from app.integrations.job_sources.naukri_connector import NaukriConnector
from app.integrations.job_sources.google_jobs_connector import GoogleJobsConnector

logger = logging.getLogger(__name__)

# ── All connectors — always-on (no key) + optional (key-based) ───
FREE_CONNECTORS = [
    RemotiveConnector(),         # Remote jobs — always works
    WeWorkRemotelyConnector(),   # Remote jobs via RSS — always works
    GreenhouseConnector(),       # 50+ top company ATS — always works
    LeverConnector(),            # 30+ top company ATS — always works
    WellfoundConnector(),        # Startup jobs — always works
    JobSpyConnector(),           # LinkedIn + Indeed + Glassdoor + Google — always works
]

OPTIONAL_CONNECTORS = [
    NaukriConnector(),           # India jobs — always works
    AdzunaConnector(),           # Needs ADZUNA_APP_ID + ADZUNA_API_KEY
    JSearchConnector(),          # Needs JSEARCH_API_KEY (RapidAPI)
    GoogleJobsConnector(),       # Needs SERPAPI_KEY (100 free/day)
]

ALL_CONNECTORS = FREE_CONNECTORS + OPTIONAL_CONNECTORS


def build_search_keywords(preferences: JobPreferences, extra_keywords: List[str] = None) -> List[str]:
    """Build comprehensive search keywords from user preferences."""
    keywords = []

    if extra_keywords:
        keywords.extend(extra_keywords)

    if preferences:
        # Add preferred job titles as primary keywords
        if preferences.preferred_titles:
            keywords.extend(preferences.preferred_titles[:5])

        # Add industries as secondary context
        if preferences.preferred_industries:
            keywords.extend(preferences.preferred_industries[:2])

    # Remove duplicates preserving order
    seen = set()
    unique = []
    for k in keywords:
        kl = k.lower().strip()
        if kl and kl not in seen:
            seen.add(kl)
            unique.append(k)

    return unique or ["software engineer"]


def compute_job_fingerprint(listing: JobListing) -> str:
    """Deduplication hash — title + company + URL."""
    text = (
        listing.title.lower().strip() +
        listing.company.lower().strip() +
        listing.apply_url.lower().strip()
    )
    return hashlib.md5(text.encode()).hexdigest()


def listing_to_job(listing: JobListing, fingerprint: str) -> Job:
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


def _run_connector(connector, keywords, location, remote_only, limit):
    """Run a single connector safely."""
    name = connector.name
    try:
        if not connector.is_configured():
            return name, [], f"{name} not configured — add API key in .env"
        listings = connector.search(
            keywords=keywords,
            location=location,
            remote_only=remote_only,
            limit=limit,
        )
        return name, listings, None
    except Exception as e:
        logger.error(f"{name} error: {e}")
        return name, [], str(e)


def run_job_discovery(
    db: Session,
    user: User,
    keywords: Optional[List[str]] = None,
    location: Optional[str] = None,
    remote_only: bool = False,
    limit_per_source: int = 50,
    max_workers: int = 6,
) -> Dict:
    """
    Main discovery: runs all sources in parallel, deduplicates, saves.
    """
    preferences = db.query(JobPreferences).filter(
        JobPreferences.user_id == user.id
    ).first()

    # Build keywords from preferences
    final_keywords = build_search_keywords(preferences, keywords)

    # Location from preferences if not specified
    if location is None and preferences:
        cities = preferences.preferred_cities or []
        countries = preferences.preferred_countries or []
        if cities:
            location = cities[0]
        elif countries:
            location = countries[0]

    # Remote preference
    if remote_only is False and preferences:
        remote_only = bool(preferences.remote_ok and not preferences.onsite_ok)

    logger.info(f"Discovery: keywords={final_keywords}, location={location}, remote={remote_only}")

    all_listings: List[JobListing] = []
    source_results = {}

    # Run all connectors in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_run_connector, conn, final_keywords, location, remote_only, limit_per_source): conn
            for conn in ALL_CONNECTORS
        }
        for future in concurrent.futures.as_completed(futures, timeout=60):
            try:
                name, listings, error = future.result()
                if error and not listings:
                    source_results[name] = {"status": "not_configured" if "configured" in error.lower() else "error",
                                             "count": 0, "message": error}
                else:
                    all_listings.extend(listings)
                    source_results[name] = {"status": "success", "count": len(listings)}
                    logger.info(f"{name}: {len(listings)} listings")
            except Exception as e:
                logger.error(f"Connector future error: {e}")

    # ── Deduplication & save ──────────────────────────────────────
    seen_fingerprints = set()
    new_jobs = 0
    duplicate_jobs = 0

    # Load existing fingerprints from DB for fast lookup
    existing_fps = {j.external_id for j in db.query(Job.external_id).all()}

    for listing in all_listings:
        if not listing.title or not listing.apply_url:
            continue

        fp = compute_job_fingerprint(listing)

        if fp in seen_fingerprints or fp in existing_fps:
            duplicate_jobs += 1
            continue

        seen_fingerprints.add(fp)

        job = listing_to_job(listing, fp)
        db.add(job)
        db.flush()

        for skill in (listing.skills_required or [])[:20]:
            if skill and skill.strip():
                db.add(JobSkill(job_id=job.id, skill_name=skill[:255], is_required=True))
        for skill in (listing.skills_preferred or [])[:10]:
            if skill and skill.strip():
                db.add(JobSkill(job_id=job.id, skill_name=skill[:255], is_required=False))

        new_jobs += 1

    db.commit()

    return {
        "total_fetched": len(all_listings),
        "new_jobs_saved": new_jobs,
        "duplicates_skipped": duplicate_jobs,
        "sources": source_results,
        "keywords_used": final_keywords,
    }


def run_targeted_company_search(
    db: Session,
    user: User,
    company_websites: List[str],
    keywords: Optional[List[str]] = None,
) -> Dict:
    """
    Targeted search: crawl specific company career pages.
    Used by Company Intelligence + Preferred Companies feature.
    """
    from app.integrations.job_sources.career_crawler import CareerPageCrawler
    from urllib.parse import urlparse

    preferences = db.query(JobPreferences).filter(
        JobPreferences.user_id == user.id
    ).first()
    final_keywords = build_search_keywords(preferences, keywords)

    all_listings = []
    results = {}

    for website in company_websites:
        try:
            parsed = urlparse(website)
            company_name = parsed.netloc.replace("www.", "").split(".")[0].title()

            crawler = CareerPageCrawler(company_name=company_name, website=website)
            listings = crawler.crawl_company(website, company_name, final_keywords, limit=30)
            all_listings.extend(listings)
            results[company_name] = len(listings)
            logger.info(f"Career crawl {company_name}: {len(listings)} jobs")
        except Exception as e:
            logger.error(f"Career crawl error {website}: {e}")

    # Save to DB
    new_jobs = 0
    existing_fps = {j.external_id for j in db.query(Job.external_id).all()}

    for listing in all_listings:
        if not listing.title or not listing.apply_url:
            continue
        fp = compute_job_fingerprint(listing)
        if fp in existing_fps:
            continue
        existing_fps.add(fp)
        job = listing_to_job(listing, fp)
        db.add(job)
        new_jobs += 1

    db.commit()
    return {"new_jobs_saved": new_jobs, "by_company": results}


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
    min_salary: Optional[float] = None,
    max_experience: Optional[int] = None,
) -> Dict:
    """Paginated job listing with comprehensive filters."""
    query = db.query(Job).filter(Job.is_active == is_active)

    if search:
        query = query.filter(
            Job.title.ilike(f"%{search}%") |
            Job.company.ilike(f"%{search}%") |
            Job.description.ilike(f"%{search}%")
        )
    if location:
        query = query.filter(
            Job.location.ilike(f"%{location}%") |
            Job.country.ilike(f"%{location}%") |
            Job.city.ilike(f"%{location}%")
        )
    if employment_type:
        query = query.filter(Job.employment_type.ilike(f"%{employment_type}%"))
    if source:
        query = query.filter(Job.source.ilike(f"%{source}%"))
    if work_mode == "remote":
        query = query.filter(Job.is_remote == True)
    elif work_mode == "hybrid":
        query = query.filter(Job.is_hybrid == True)
    elif work_mode == "onsite":
        query = query.filter(Job.is_remote == False, Job.is_hybrid == False)
    if min_salary:
        query = query.filter(Job.salary_max >= min_salary)

    sort_map = {
        "-posted_at": Job.posted_at.desc(),
        "posted_at": Job.posted_at.asc(),
        "-salary_max": Job.salary_max.desc(),
        "salary_max": Job.salary_max.asc(),
        "title": Job.title.asc(),
        "company": Job.company.asc(),
        "-created_at": Job.created_at.desc(),
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
