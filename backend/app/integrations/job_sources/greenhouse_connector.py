"""
Greenhouse ATS Connector — fetches real job postings directly from
company Greenhouse boards. No API key needed. Public JSON API.
Covers thousands of companies: Airbnb, Stripe, Figma, Notion, etc.
"""
import logging
import requests
import time
from typing import List, Optional
from datetime import datetime
from app.integrations.job_sources.base import BaseJobSource, JobListing

logger = logging.getLogger(__name__)

# Top companies using Greenhouse — their board token
GREENHOUSE_COMPANIES = [
    # Tech giants & unicorns
    ("Airbnb", "airbnb"), ("Stripe", "stripe"), ("Figma", "figma"),
    ("Notion", "notion"), ("Canva", "canva"), ("Shopify", "shopify"),
    ("Dropbox", "dropbox"), ("Twilio", "twilio"), ("Datadog", "datadoghq"),
    ("Snowflake", "snowflake"), ("MongoDB", "mongodb"), ("HashiCorp", "hashicorp"),
    ("Confluent", "confluent"), ("Databricks", "databricks"), ("Cockroach Labs", "cockroachlabs"),
    ("Vercel", "vercel"), ("Netlify", "netlify"), ("PlanetScale", "planetscale"),
    ("Railway", "railway"), ("Fly.io", "flydotio"),
    # Finance & Payments
    ("Plaid", "plaid"), ("Brex", "brex"), ("Ramp", "ramp"), ("Mercury", "mercury"),
    ("Chime", "chime"), ("Robinhood", "robinhood"), ("Coinbase", "coinbase"),
    # AI Companies
    ("OpenAI", "openai"), ("Anthropic", "anthropic"), ("Cohere", "cohere"),
    ("Scale AI", "scaleai"), ("Hugging Face", "huggingface"),
    ("Stability AI", "stability"), ("Mistral AI", "mistral"),
    # Enterprise
    ("Asana", "asana"), ("Airtable", "airtable"), ("Miro", "miro"),
    ("Linear", "linear"), ("Loom", "loom"), ("Calendly", "calendly"),
    ("Zapier", "zapier"), ("Webflow", "webflow"), ("Intercom", "intercom"),
    # Health & Bio
    ("Oscar Health", "oscar"), ("Noom", "noom"), ("Hims Hers", "himshers"),
    # E-commerce
    ("Faire", "faire"), ("Whatnot", "whatnot"), ("Poshmark", "poshmark"),
]


class GreenhouseConnector(BaseJobSource):
    name = "Greenhouse"
    requires_api_key = False

    def is_configured(self) -> bool:
        return True

    def search(
        self,
        keywords: List[str],
        location: Optional[str] = None,
        remote_only: bool = False,
        limit: int = 100,
        companies: Optional[List[str]] = None,
    ) -> List[JobListing]:

        keyword_set = {k.lower() for k in keywords}
        results = []

        # Use specific companies or scan all
        targets = GREENHOUSE_COMPANIES[:30]  # limit to avoid rate limits

        for company_name, board_token in targets:
            if len(results) >= limit:
                break
            try:
                url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"
                r = requests.get(url, params={"content": "true"}, timeout=10)
                if r.status_code != 200:
                    continue
                data = r.json()
                for job in data.get("jobs", []):
                    title = job.get("title", "").lower()
                    # Filter by keywords
                    if keyword_set and not any(kw in title for kw in keyword_set):
                        continue
                    # Filter by location if specified
                    job_location = job.get("location", {}).get("name", "")
                    if location and location.lower() not in job_location.lower() and not remote_only:
                        if "remote" not in job_location.lower():
                            continue
                    listing = self._normalize(job, company_name)
                    if listing:
                        results.append(listing)
                time.sleep(0.3)  # polite rate limiting
            except Exception as e:
                logger.debug(f"Greenhouse {company_name}: {e}")
                continue

        logger.info(f"Greenhouse: found {len(results)} jobs")
        return results[:limit]

    def _normalize(self, job: dict, company_name: str) -> Optional[JobListing]:
        try:
            title = job.get("title", "")
            location = job.get("location", {}).get("name", "")
            apply_url = job.get("absolute_url", "")
            if not title or not apply_url:
                return None

            # Parse date
            posted_at = None
            updated = job.get("updated_at") or job.get("created_at")
            if updated:
                try:
                    posted_at = datetime.fromisoformat(updated.replace("Z", "+00:00"))
                except Exception:
                    pass

            # Extract description from content
            content = job.get("content", "")
            description = content[:5000] if content else f"{title} at {company_name}"

            is_remote = "remote" in location.lower()

            return JobListing(
                title=title,
                company=company_name,
                location=location or "See job posting",
                description=description,
                apply_url=apply_url,
                source="Greenhouse",
                external_id=str(job.get("id", "")),
                is_remote=is_remote,
                employment_type="Full-time",
                posted_at=posted_at,
            )
        except Exception as e:
            logger.debug(f"Greenhouse normalize error: {e}")
            return None
