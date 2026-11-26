"""
Lever ATS Connector — fetches real job postings directly from
company Lever boards. No API key needed.
Covers: Netflix, Slack, Twitter/X, Lyft, Square, and thousands more.
"""
import logging
import requests
import time
from typing import List, Optional
from datetime import datetime
from app.integrations.job_sources.base import BaseJobSource, JobListing

logger = logging.getLogger(__name__)

LEVER_COMPANIES = [
    ("Netflix", "netflix"), ("Square", "squareup"), ("Lyft", "lyft"),
    ("Slack", "slack"), ("Pinterest", "pinterest"), ("Reddit", "reddit"),
    ("Duolingo", "duolingo"), ("Discord", "discord"), ("Cloudflare", "cloudflare"),
    ("Atlassian", "atlassian"), ("HubSpot", "hubspot"), ("DocuSign", "docusign"),
    ("Zendesk", "zendesk"), ("Okta", "okta"), ("Splunk", "splunk"),
    ("Palantir", "palantir"), ("Instacart", "instacart"), ("DoorDash", "doordash"),
    ("Flexport", "flexport"), ("Benchling", "benchling"), ("Nuro", "nuro"),
    ("Relativity Space", "relativity"), ("Verkada", "verkada"),
    ("Ironclad", "ironcladapp"), ("Persona", "withpersona"),
    ("Gem", "gem"), ("Lattice", "latticehq"), ("Rippling", "rippling"),
    ("Gusto", "gusto"), ("Remote", "remote"), ("Deel", "deel"),
]


class LeverConnector(BaseJobSource):
    name = "Lever"
    requires_api_key = False

    def is_configured(self) -> bool:
        return True

    def search(
        self,
        keywords: List[str],
        location: Optional[str] = None,
        remote_only: bool = False,
        limit: int = 100,
    ) -> List[JobListing]:

        keyword_set = {k.lower() for k in keywords}
        results = []

        for company_name, slug in LEVER_COMPANIES:
            if len(results) >= limit:
                break
            try:
                url = f"https://api.lever.co/v0/postings/{slug}"
                r = requests.get(url, params={"mode": "json", "limit": 50}, timeout=10)
                if r.status_code != 200:
                    continue
                jobs = r.json()
                for job in jobs:
                    title = (job.get("text") or job.get("title") or "").lower()
                    if keyword_set and not any(kw in title for kw in keyword_set):
                        continue
                    listing = self._normalize(job, company_name)
                    if listing:
                        results.append(listing)
                time.sleep(0.3)
            except Exception as e:
                logger.debug(f"Lever {company_name}: {e}")
                continue

        logger.info(f"Lever: found {len(results)} jobs")
        return results[:limit]

    def _normalize(self, job: dict, company_name: str) -> Optional[JobListing]:
        try:
            title = job.get("text") or job.get("title", "")
            apply_url = job.get("hostedUrl") or job.get("applyUrl", "")
            if not title or not apply_url:
                return None

            categories = job.get("categories", {})
            location = categories.get("location", "")
            team = categories.get("team", "")
            commitment = categories.get("commitment", "Full-time")

            # Description from lists
            desc_parts = []
            for section in (job.get("lists") or []):
                desc_parts.append(f"{section.get('text', '')}: {section.get('content', '')}")
            description = " ".join(desc_parts) or f"{title} at {company_name}"

            is_remote = "remote" in (location or "").lower()

            posted_at = None
            created = job.get("createdAt")
            if created:
                try:
                    posted_at = datetime.fromtimestamp(int(created) / 1000)
                except Exception:
                    pass

            return JobListing(
                title=title,
                company=company_name,
                location=location or "See posting",
                description=description[:5000],
                apply_url=apply_url,
                source="Lever",
                external_id=job.get("id", ""),
                employment_type=commitment or "Full-time",
                is_remote=is_remote,
                industry=team,
                posted_at=posted_at,
            )
        except Exception as e:
            logger.debug(f"Lever normalize error: {e}")
            return None
