"""
Adzuna Job API connector.
Free tier available at: https://developer.adzuna.com/
Provides access to real job listings.
"""
import logging
import requests
from typing import List, Optional
from datetime import datetime
from app.core.config import settings
from app.integrations.job_sources.base import BaseJobSource, JobListing

logger = logging.getLogger(__name__)

ADZUNA_API_BASE = "https://api.adzuna.com/v1/api/jobs"

COUNTRY_CODES = {
    "us": "us", "uk": "gb", "gb": "gb", "ca": "ca",
    "au": "au", "de": "de", "fr": "fr", "in": "in",
    "nz": "nz", "za": "za",
}


class AdzunaConnector(BaseJobSource):
    name = "Adzuna"
    requires_api_key = True

    def is_configured(self) -> bool:
        return bool(settings.ADZUNA_APP_ID and settings.ADZUNA_API_KEY)

    def search(
        self,
        keywords: List[str],
        location: Optional[str] = None,
        remote_only: bool = False,
        limit: int = 50,
        country: str = "us",
    ) -> List[JobListing]:
        if not self.is_configured():
            logger.warning("Adzuna not configured — skipping. Set ADZUNA_APP_ID and ADZUNA_API_KEY.")
            return []

        country_code = COUNTRY_CODES.get(country.lower(), "us")
        query = " ".join(keywords)
        if remote_only:
            query += " remote"

        params = {
            "app_id": settings.ADZUNA_APP_ID,
            "app_key": settings.ADZUNA_API_KEY,
            "results_per_page": min(limit, 50),
            "what": query,
            "content-type": "application/json",
        }
        if location:
            params["where"] = location

        try:
            url = f"{ADZUNA_API_BASE}/{country_code}/search/1"
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            return [self._normalize(job) for job in data.get("results", [])]
        except requests.RequestException as e:
            logger.error(f"Adzuna API error: {e}")
            return []

    def _normalize(self, raw: dict) -> JobListing:
        salary_min = raw.get("salary_min")
        salary_max = raw.get("salary_max")
        created = raw.get("created")
        posted_at = None
        if created:
            try:
                posted_at = datetime.fromisoformat(created.replace("Z", "+00:00"))
            except ValueError:
                pass

        location_data = raw.get("location", {})
        display_location = location_data.get("display_name", "")

        return JobListing(
            title=raw.get("title", ""),
            company=raw.get("company", {}).get("display_name", "Unknown"),
            location=display_location,
            description=raw.get("description", ""),
            apply_url=raw.get("redirect_url", ""),
            source="Adzuna",
            external_id=str(raw.get("id", "")),
            salary_min=float(salary_min) if salary_min else None,
            salary_max=float(salary_max) if salary_max else None,
            employment_type=raw.get("contract_type", ""),
            posted_at=posted_at,
            is_remote="remote" in display_location.lower() or "remote" in raw.get("title", "").lower(),
        )
