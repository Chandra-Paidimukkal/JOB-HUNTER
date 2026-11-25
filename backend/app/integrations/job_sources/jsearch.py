"""
JSearch API connector (via RapidAPI) — aggregates LinkedIn, Indeed, Glassdoor etc.
Get key at: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
"""
import logging
import requests
from typing import List, Optional
from datetime import datetime
from app.core.config import settings
from app.integrations.job_sources.base import BaseJobSource, JobListing

logger = logging.getLogger(__name__)


class JSearchConnector(BaseJobSource):
    name = "JSearch"
    requires_api_key = True

    def is_configured(self) -> bool:
        return bool(settings.JSEARCH_API_KEY)

    def search(
        self,
        keywords: List[str],
        location: Optional[str] = None,
        remote_only: bool = False,
        limit: int = 50,
    ) -> List[JobListing]:
        if not self.is_configured():
            logger.warning("JSearch not configured — skipping. Set JSEARCH_API_KEY.")
            return []

        query = " ".join(keywords)
        if remote_only:
            query += " remote"
        if location:
            query += f" in {location}"

        try:
            response = requests.get(
                "https://jsearch.p.rapidapi.com/search",
                params={
                    "query": query,
                    "num_pages": str(max(1, limit // 10)),
                    "page": "1",
                },
                headers={
                    "X-RapidAPI-Key": settings.JSEARCH_API_KEY,
                    "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
                },
                timeout=20,
            )
            response.raise_for_status()
            data = response.json()
            return [self._normalize(job) for job in data.get("data", [])[:limit]]
        except requests.RequestException as e:
            logger.error(f"JSearch API error: {e}")
            return []

    def _normalize(self, raw: dict) -> JobListing:
        # Salary
        salary_min = raw.get("job_min_salary")
        salary_max = raw.get("job_max_salary")
        currency = raw.get("job_salary_currency", "USD")

        # Date
        posted_at = None
        ts = raw.get("job_posted_at_timestamp")
        if ts:
            try:
                posted_at = datetime.fromtimestamp(int(ts))
            except (ValueError, TypeError):
                pass

        is_remote = raw.get("job_is_remote", False)

        return JobListing(
            title=raw.get("job_title", ""),
            company=raw.get("employer_name", ""),
            company_logo=raw.get("employer_logo"),
            location=f"{raw.get('job_city', '')}, {raw.get('job_country', '')}".strip(", "),
            country=raw.get("job_country"),
            city=raw.get("job_city"),
            description=raw.get("job_description", ""),
            apply_url=raw.get("job_apply_link", ""),
            source="JSearch",
            external_id=raw.get("job_id", ""),
            employment_type=raw.get("job_employment_type", ""),
            salary_min=float(salary_min) if salary_min else None,
            salary_max=float(salary_max) if salary_max else None,
            salary_currency=currency,
            is_remote=is_remote,
            is_hybrid="hybrid" in raw.get("job_employment_type", "").lower(),
            posted_at=posted_at,
            skills_required=raw.get("job_required_skills") or [],
            requirements=raw.get("job_highlights", {}).get("Qualifications", []),
        )
