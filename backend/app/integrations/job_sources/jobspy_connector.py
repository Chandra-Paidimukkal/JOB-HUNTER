"""
JobSpy2 Connector — scrapes LinkedIn, Indeed, Glassdoor, Google Jobs, ZipRecruiter
simultaneously. No API keys needed. Uses jobspy2 library.

This is the MAIN engine for global job search.
"""
import logging
import time
from typing import List, Optional
from datetime import datetime, timedelta
from app.integrations.job_sources.base import BaseJobSource, JobListing

logger = logging.getLogger(__name__)


class JobSpyConnector(BaseJobSource):
    """
    Scrapes LinkedIn, Indeed, Glassdoor, Google Jobs, ZipRecruiter, Naukri.
    Uses jobspy2 which handles anti-bot measures automatically.
    """
    name = "JobSpy"
    requires_api_key = False

    def is_configured(self) -> bool:
        return True  # No key needed

    def search(
        self,
        keywords: List[str],
        location: Optional[str] = None,
        remote_only: bool = False,
        limit: int = 100,
        country: str = "USA",
        hours_old: int = 72,
    ) -> List[JobListing]:
        try:
            from jobspy2 import scrape_jobs
            import pandas as pd

            query = " ".join(keywords)
            search_location = location or ("Remote" if remote_only else "United States")

            logger.info(f"JobSpy scraping: '{query}' in '{search_location}'")

            # Scrape from multiple sites — exclude Glassdoor (needs login) and ZipRecruiter (blocks)
            df = scrape_jobs(
                site_name=["linkedin", "indeed"],
                search_term=query,
                location=search_location,
                results_wanted=min(limit, 20),
                hours_old=hours_old,
                country_indeed=country,
                linkedin_fetch_description=False,  # Faster without full description
                verbose=0,
            )

            if df is None or df.empty:
                logger.warning("JobSpy returned no results")
                return []

            listings = []
            for _, row in df.iterrows():
                try:
                    listing = self._normalize(row)
                    if listing and listing.title and listing.company:
                        listings.append(listing)
                except Exception as e:
                    logger.debug(f"Row normalize error: {e}")
                    continue

            logger.info(f"JobSpy fetched {len(listings)} listings")
            return listings

        except ImportError:
            logger.error("jobspy2 not installed. Run: pip install jobspy2")
            return []
        except Exception as e:
            logger.error(f"JobSpy scraping error: {e}")
            return []

    def _normalize(self, row) -> Optional[JobListing]:
        import pandas as pd

        def safe_str(val, default="") -> str:
            if pd.isna(val) or val is None:
                return default
            return str(val).strip()

        def safe_float(val) -> Optional[float]:
            try:
                if pd.isna(val) or val is None:
                    return None
                return float(val)
            except Exception:
                return None

        def safe_date(val) -> Optional[datetime]:
            try:
                if pd.isna(val) or val is None:
                    return None
                if isinstance(val, datetime):
                    return val
                return pd.to_datetime(val).to_pydatetime()
            except Exception:
                return None

        title = safe_str(row.get("title"))
        company = safe_str(row.get("company"))
        if not title or not company:
            return None

        location = safe_str(row.get("location"))
        is_remote = "remote" in location.lower() or safe_str(row.get("is_remote")).lower() == "true"

        return JobListing(
            title=title,
            company=company,
            company_logo=safe_str(row.get("company_logo")),
            location=location,
            country=safe_str(row.get("country")),
            city=safe_str(row.get("city")),
            description=safe_str(row.get("description", "No description available")),
            apply_url=safe_str(row.get("job_url")) or safe_str(row.get("job_url_direct")),
            source=safe_str(row.get("site"), "JobSpy").title(),
            external_id=safe_str(row.get("id")),
            employment_type=safe_str(row.get("job_type", "Full-time")),
            salary_min=safe_float(row.get("min_amount")),
            salary_max=safe_float(row.get("max_amount")),
            salary_currency=safe_str(row.get("currency", "USD")),
            is_remote=is_remote,
            is_hybrid="hybrid" in safe_str(row.get("job_type", "")).lower(),
            posted_at=safe_date(row.get("date_posted")),
            skills_required=[],
            industry=safe_str(row.get("industry")),
        )
