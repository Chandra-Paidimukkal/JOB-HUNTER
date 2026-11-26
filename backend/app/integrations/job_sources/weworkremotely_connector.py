"""
We Work Remotely Connector — top remote job board.
Public RSS feed available, no key needed.
"""
import logging
import requests
import xml.etree.ElementTree as ET
from typing import List, Optional
from datetime import datetime
from app.integrations.job_sources.base import BaseJobSource, JobListing

logger = logging.getLogger(__name__)

WWR_CATEGORIES = [
    "https://weworkremotely.com/remote-jobs.rss",
    "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
    "https://weworkremotely.com/categories/remote-management-and-finance-jobs.rss",
    "https://weworkremotely.com/categories/remote-product-jobs.rss",
    "https://weworkremotely.com/categories/remote-design-jobs.rss",
    "https://weworkremotely.com/categories/remote-data-science-ai-jobs.rss",
]


class WeWorkRemotelyConnector(BaseJobSource):
    name = "WeWorkRemotely"
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
        keyword_set = {k.lower() for k in keywords}
        results = []

        for feed_url in WWR_CATEGORIES:
            if len(results) >= limit:
                break
            try:
                r = requests.get(feed_url, timeout=10, headers={
                    "User-Agent": "Mozilla/5.0 JobHunter/1.0"
                })
                if r.status_code != 200:
                    continue

                root = ET.fromstring(r.content)
                channel = root.find("channel")
                if not channel:
                    continue

                for item in channel.findall("item"):
                    title = (item.findtext("title") or "").strip()
                    if keyword_set and not any(kw in title.lower() for kw in keyword_set):
                        continue

                    listing = self._normalize(item)
                    if listing:
                        results.append(listing)
                        if len(results) >= limit:
                            break

            except Exception as e:
                logger.debug(f"WWR feed {feed_url}: {e}")
                continue

        logger.info(f"WeWorkRemotely: found {len(results)} jobs")
        return results[:limit]

    def _normalize(self, item) -> Optional[JobListing]:
        try:
            full_title = item.findtext("title") or ""
            link = item.findtext("link") or ""
            description = item.findtext("description") or ""
            pub_date_str = item.findtext("pubDate") or ""

            # Title format: "Company Name: Job Title"
            if ":" in full_title:
                parts = full_title.split(":", 1)
                company = parts[0].strip()
                title = parts[1].strip()
            else:
                company = "Unknown"
                title = full_title.strip()

            if not title or not link:
                return None

            # Clean description HTML
            import re
            clean_desc = re.sub(r"<[^>]+>", " ", description).strip()
            clean_desc = re.sub(r"\s+", " ", clean_desc)

            posted_at = None
            if pub_date_str:
                try:
                    from email.utils import parsedate_to_datetime
                    posted_at = parsedate_to_datetime(pub_date_str)
                except Exception:
                    pass

            return JobListing(
                title=title,
                company=company,
                location="Remote (Worldwide)",
                description=clean_desc[:5000],
                apply_url=link,
                source="WeWorkRemotely",
                external_id=item.findtext("guid") or link,
                employment_type="Full-time",
                is_remote=True,
                posted_at=posted_at,
            )
        except Exception as e:
            logger.debug(f"WWR normalize error: {e}")
            return None
