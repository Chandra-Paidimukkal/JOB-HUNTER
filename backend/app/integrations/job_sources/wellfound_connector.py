"""
Wellfound (AngelList) Connector — startup & tech jobs.
Uses the public GraphQL API + direct scraping.
"""
import logging
import requests
import time
from typing import List, Optional
from datetime import datetime
from app.integrations.job_sources.base import BaseJobSource, JobListing

logger = logging.getLogger(__name__)


class WellfoundConnector(BaseJobSource):
    name = "Wellfound"
    requires_api_key = False

    def is_configured(self) -> bool:
        return True

    def search(
        self,
        keywords: List[str],
        location: Optional[str] = None,
        remote_only: bool = False,
        limit: int = 50,
    ) -> List[JobListing]:
        try:
            query = " ".join(keywords)
            # Wellfound public API (no auth needed for browsing)
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
                "Referer": "https://wellfound.com",
            }

            # Use their search endpoint
            search_url = "https://wellfound.com/api/graphql"
            graphql_query = {
                "query": """
                query JobListingsSearch($query: String!, $page: Int) {
                  jobListings(query: $query, page: $page) {
                    items {
                      id
                      title
                      description
                      jobTypes
                      remote
                      locationNames
                      slug
                      compensation
                      createdAt
                      startup {
                        name
                        logoUrl
                        websiteUrl
                        markets { displayName }
                      }
                    }
                  }
                }
                """,
                "variables": {"query": query, "page": 1},
            }

            r = requests.post(search_url, json=graphql_query, headers=headers, timeout=15)

            if r.status_code == 200:
                data = r.json()
                items = (
                    data.get("data", {})
                    .get("jobListings", {})
                    .get("items", [])
                )
                results = []
                for item in items[:limit]:
                    listing = self._normalize(item)
                    if listing:
                        results.append(listing)
                logger.info(f"Wellfound: found {len(results)} jobs")
                return results

        except Exception as e:
            logger.error(f"Wellfound error: {e}")

        # Fallback to scraping
        return self._scrape_fallback(keywords, location, limit)

    def _scrape_fallback(self, keywords, location, limit) -> List[JobListing]:
        """Fallback: scrape Wellfound search results page."""
        try:
            from bs4 import BeautifulSoup
            query = "+".join(keywords)
            url = f"https://wellfound.com/jobs?query={query}"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code != 200:
                return []

            soup = BeautifulSoup(r.text, "html.parser")
            results = []

            for card in soup.select("[data-test='JobListingCard']")[:limit]:
                try:
                    title_el = card.select_one("[data-test='JobListingTitle']")
                    company_el = card.select_one("[data-test='StartupName']")
                    link_el = card.select_one("a")
                    if not title_el or not company_el:
                        continue
                    href = link_el.get("href", "") if link_el else ""
                    apply_url = f"https://wellfound.com{href}" if href.startswith("/") else href

                    results.append(JobListing(
                        title=title_el.get_text(strip=True),
                        company=company_el.get_text(strip=True),
                        location="Remote",
                        description=f"{title_el.get_text(strip=True)} at {company_el.get_text(strip=True)}",
                        apply_url=apply_url,
                        source="Wellfound",
                        is_remote=True,
                    ))
                except Exception:
                    continue
            return results
        except Exception as e:
            logger.error(f"Wellfound fallback error: {e}")
            return []

    def _normalize(self, item: dict) -> Optional[JobListing]:
        try:
            startup = item.get("startup") or {}
            title = item.get("title", "")
            company = startup.get("name", "")
            if not title or not company:
                return None

            slug = item.get("slug", "")
            apply_url = f"https://wellfound.com/jobs/{slug}" if slug else ""

            locations = item.get("locationNames") or []
            location = ", ".join(locations) if locations else ("Remote" if item.get("remote") else "")

            markets = startup.get("markets") or []
            industry = ", ".join(m.get("displayName", "") for m in markets[:2])

            posted_at = None
            created = item.get("createdAt")
            if created:
                try:
                    posted_at = datetime.fromisoformat(created.replace("Z", "+00:00"))
                except Exception:
                    pass

            comp = item.get("compensation") or {}
            salary_min = comp.get("minAmount") if isinstance(comp, dict) else None
            salary_max = comp.get("maxAmount") if isinstance(comp, dict) else None

            return JobListing(
                title=title,
                company=company,
                company_logo=startup.get("logoUrl"),
                location=location or "Global",
                description=item.get("description", "")[:5000],
                apply_url=apply_url,
                source="Wellfound",
                external_id=str(item.get("id", "")),
                employment_type=", ".join(item.get("jobTypes") or ["Full-time"]),
                is_remote=bool(item.get("remote")),
                salary_min=float(salary_min) if salary_min else None,
                salary_max=float(salary_max) if salary_max else None,
                industry=industry,
                posted_at=posted_at,
            )
        except Exception as e:
            logger.debug(f"Wellfound normalize error: {e}")
            return None
