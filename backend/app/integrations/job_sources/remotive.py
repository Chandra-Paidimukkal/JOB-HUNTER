"""
Remotive — free public API for remote jobs.
No API key required. https://remotive.com/api
"""
import logging
import requests
from typing import List, Optional
from datetime import datetime
from app.integrations.job_sources.base import BaseJobSource, JobListing

logger = logging.getLogger(__name__)


class RemotiveConnector(BaseJobSource):
    name = "Remotive"
    requires_api_key = False

    def is_configured(self) -> bool:
        return True  # No key required

    def search(
        self,
        keywords: List[str],
        location: Optional[str] = None,
        remote_only: bool = False,
        limit: int = 50,
    ) -> List[JobListing]:
        query = " ".join(keywords)
        try:
            response = requests.get(
                "https://remotive.com/api/remote-jobs",
                params={"search": query, "limit": min(limit, 100)},
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()
            return [self._normalize(job) for job in data.get("jobs", [])[:limit]]
        except requests.RequestException as e:
            logger.error(f"Remotive API error: {e}")
            return []

    def _normalize(self, raw: dict) -> JobListing:
        pub_date = raw.get("publication_date", "")
        posted_at = None
        if pub_date:
            try:
                posted_at = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
            except ValueError:
                pass

        return JobListing(
            title=raw.get("title", ""),
            company=raw.get("company_name", ""),
            company_logo=raw.get("company_logo_url"),
            location=raw.get("candidate_required_location", "Remote"),
            description=raw.get("description", ""),
            apply_url=raw.get("url", ""),
            source="Remotive",
            external_id=str(raw.get("id", "")),
            employment_type=raw.get("job_type", "Full-time"),
            salary_min=None,
            salary_max=None,
            is_remote=True,
            posted_at=posted_at,
            skills_required=raw.get("tags", []),
            industry=raw.get("category", ""),
        )
