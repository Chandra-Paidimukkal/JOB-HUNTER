"""
Naukri.com Connector — India's largest job portal.
Scrapes search results from Naukri public search pages.
"""
import logging
import requests
import time
import json
import re
from typing import List, Optional
from datetime import datetime
from app.integrations.job_sources.base import BaseJobSource, JobListing

logger = logging.getLogger(__name__)


class NaukriConnector(BaseJobSource):
    name = "Naukri"
    requires_api_key = False

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.naukri.com/",
        "appid": "109",
        "systemid": "109",
        "gid": "LOCATION,INDUSTRY,EDUCATION,FAREA_ROLE",
        "Content-Type": "application/json",
    }

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
            query = "%20".join(keywords)
            loc_param = location.replace(" ", "%20") if location else ""

            # Naukri API endpoint
            url = "https://www.naukri.com/jobapi/v3/search"
            params = {
                "noOfResults": min(limit, 50),
                "urlType": "search_by_keyword",
                "searchType": "adv",
                "keyword": " ".join(keywords),
                "location": location or "",
                "k": " ".join(keywords),
                "l": location or "",
                "experience": "",
                "sort": "1",  # newest
                "pageNo": "1",
            }

            r = requests.get(url, params=params, headers=self.HEADERS, timeout=15)

            if r.status_code == 200:
                data = r.json()
                jobs = data.get("jobDetails", [])
                results = [self._normalize(j) for j in jobs if j]
                results = [r for r in results if r]
                logger.info(f"Naukri: found {len(results)} jobs")
                return results[:limit]
            else:
                logger.warning(f"Naukri API returned {r.status_code}")
                return self._scrape_fallback(keywords, location, limit)

        except Exception as e:
            logger.error(f"Naukri error: {e}")
            return self._scrape_fallback(keywords, location, limit)

    def _scrape_fallback(self, keywords, location, limit) -> List[JobListing]:
        """Scrape Naukri search results page as fallback."""
        try:
            from bs4 import BeautifulSoup
            query = "-".join(k.lower().replace(" ", "-") for k in keywords)
            loc = f"-in-{location.lower().replace(' ', '-')}" if location else ""
            url = f"https://www.naukri.com/{query}-jobs{loc}"

            r = requests.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }, timeout=15)
            if r.status_code != 200:
                return []

            soup = BeautifulSoup(r.text, "html.parser")
            results = []

            for card in soup.select(".jobTuple, .job-tuple, [data-job-id]")[:limit]:
                try:
                    title_el = card.select_one(".title, .jobTitle, h2 a, h3 a")
                    company_el = card.select_one(".subTitle, .companyInfo, .company-name")
                    link_el = card.select_one("a.title, a.jobTitle, h2 a")

                    if not title_el:
                        continue

                    title = title_el.get_text(strip=True)
                    company = company_el.get_text(strip=True) if company_el else "Unknown"
                    href = link_el.get("href", "") if link_el else ""
                    apply_url = href if href.startswith("http") else f"https://www.naukri.com{href}"

                    loc_el = card.select_one(".location, .locWdth, .loc")
                    loc_text = loc_el.get_text(strip=True) if loc_el else ""

                    results.append(JobListing(
                        title=title,
                        company=company,
                        location=loc_text or "India",
                        description=f"{title} at {company}. Apply on Naukri.",
                        apply_url=apply_url,
                        source="Naukri",
                    ))
                except Exception:
                    continue
            return results
        except Exception as e:
            logger.error(f"Naukri fallback scraping error: {e}")
            return []

    def _normalize(self, job: dict) -> Optional[JobListing]:
        try:
            title = job.get("title", "")
            company = job.get("companyName", "")
            if not title or not company:
                return None

            job_id = job.get("jobId", "")
            apply_url = job.get("jdURL") or f"https://www.naukri.com/job-listings-{job_id}"

            locations = job.get("placeholders", [])
            location_text = ""
            exp_text = ""
            for ph in locations:
                if ph.get("type") == "location":
                    location_text = ph.get("label", "")
                elif ph.get("type") == "experience":
                    exp_text = ph.get("label", "")

            salary = job.get("salary", "")

            # Extract salary range
            salary_min = salary_max = None
            sal_match = re.search(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*Lakh", salary, re.I)
            if sal_match:
                # Convert Lakhs to USD approximately
                salary_min = float(sal_match.group(1)) * 1200
                salary_max = float(sal_match.group(2)) * 1200

            posted_at = None
            created = job.get("footerPlaceholderLabel") or job.get("modifiedOn")

            return JobListing(
                title=title,
                company=company,
                company_logo=job.get("companyImageUrl"),
                location=location_text or "India",
                country="India",
                description=job.get("jobDescription", f"{title} at {company}")[:5000],
                apply_url=apply_url,
                source="Naukri",
                external_id=str(job_id),
                employment_type=job.get("employmentType", "Full-time"),
                salary_min=salary_min,
                salary_max=salary_max,
                salary_currency="INR",
                is_remote="remote" in location_text.lower(),
                posted_at=posted_at,
                skills_required=job.get("tagsAndSkills", "").split(",") if job.get("tagsAndSkills") else [],
            )
        except Exception as e:
            logger.debug(f"Naukri normalize error: {e}")
            return None
