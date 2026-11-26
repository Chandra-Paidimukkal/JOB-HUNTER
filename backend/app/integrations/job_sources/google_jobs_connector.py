"""
Google Jobs Connector via SerpAPI.
Google Jobs aggregates LinkedIn, Indeed, Glassdoor, ZipRecruiter, and
DIRECT COMPANY CAREER PAGES all in one search.

100 free searches/day. Get key at https://serpapi.com
Set SERPAPI_KEY in .env
"""
import logging
import requests
from typing import List, Optional
from datetime import datetime
from app.core.config import settings
from app.integrations.job_sources.base import BaseJobSource, JobListing

logger = logging.getLogger(__name__)


class GoogleJobsConnector(BaseJobSource):
    name = "Google Jobs"
    requires_api_key = True

    def is_configured(self) -> bool:
        return bool(getattr(settings, "SERPAPI_KEY", ""))

    def search(
        self,
        keywords: List[str],
        location: Optional[str] = None,
        remote_only: bool = False,
        limit: int = 50,
    ) -> List[JobListing]:
        if not self.is_configured():
            return []

        query = " ".join(keywords)
        if remote_only:
            query += " remote"

        params = {
            "engine": "google_jobs",
            "q": query,
            "location": location or "United States",
            "api_key": settings.SERPAPI_KEY,
            "num": min(limit, 50),
        }

        try:
            r = requests.get("https://serpapi.com/search", params=params, timeout=20)
            if r.status_code != 200:
                logger.error(f"SerpAPI returned {r.status_code}")
                return []

            data = r.json()
            jobs = data.get("jobs_results", [])

            results = []
            for job in jobs[:limit]:
                listing = self._normalize(job)
                if listing:
                    results.append(listing)

            logger.info(f"Google Jobs: found {len(results)} jobs")
            return results

        except Exception as e:
            logger.error(f"Google Jobs error: {e}")
            return []

    def _normalize(self, job: dict) -> Optional[JobListing]:
        try:
            title = job.get("title", "")
            company = job.get("company_name", "")
            if not title or not company:
                return None

            # Apply link — through Google redirect, direct if available
            apply_url = ""
            for option in (job.get("apply_options") or []):
                if option.get("apply_link"):
                    apply_url = option["apply_link"]
                    break
            if not apply_url:
                apply_url = job.get("job_link", "")

            # Location
            location_parts = []
            for key in ("city", "state", "country"):
                val = job.get(key)
                if val:
                    location_parts.append(val)
            location = ", ".join(location_parts) or "Remote"

            # Via which source (LinkedIn, Indeed, Glassdoor, company page...)
            via = job.get("via", "")
            if via:
                source = via.replace("via ", "").title()
            else:
                source = "Google Jobs"

            # Posted time
            posted_at = None
            detected = job.get("detected_extensions", {})
            posted_str = detected.get("posted_at") or job.get("posted_time") or ""
            if posted_str and "day" in posted_str:
                try:
                    days = int("".join(c for c in posted_str if c.isdigit()) or 0)
                    from datetime import timedelta
                    posted_at = datetime.utcnow() - timedelta(days=days)
                except Exception:
                    pass

            # Salary
            salary_str = detected.get("salary") or ""
            salary_min = salary_max = None
            import re
            salary_match = re.search(r"\$?(\d+[kK]?)\s*[-–to]+\s*\$?(\d+[kK]?)", salary_str)
            if salary_match:
                def parse_amount(amt):
                    amt = amt.strip("$kK")
                    try:
                        val = float(amt)
                        return val * 1000 if val < 1000 else val
                    except ValueError:
                        return None
                salary_min = parse_amount(salary_match.group(1))
                salary_max = parse_amount(salary_match.group(2))

            # Description
            description = job.get("description", "")

            # Job type
            job_types = detected.get("job_types") or job.get("employment_type") or "Full-time"

            is_remote = "remote" in location.lower() or "work from home" in description.lower()[:200]

            return JobListing(
                title=title,
                company=company,
                company_logo=job.get("thumbnail"),
                location=location,
                country=job.get("country"),
                city=job.get("city"),
                description=description[:5000],
                apply_url=apply_url,
                source=f"Google/{source}",
                external_id=job.get("job_id", ""),
                employment_type=job_types,
                salary_min=salary_min,
                salary_max=salary_max,
                is_remote=is_remote,
                posted_at=posted_at,
                requirements=job.get("qualifications", []),
            )
        except Exception as e:
            logger.debug(f"Google Jobs normalize error: {e}")
            return None
