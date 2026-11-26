"""
OpenWebNinja JSearch Connector
API: https://api.openwebninja.com/jsearch/search-v2
Aggregates LinkedIn, Indeed, Glassdoor, ZipRecruiter + 50 more job boards.
Key: set OPENWEBNINJA_KEY in .env
"""
import logging
import requests
import re
from typing import List, Optional
from datetime import datetime, timedelta
from app.core.config import settings
from app.integrations.job_sources.base import BaseJobSource, JobListing

logger = logging.getLogger(__name__)

BASE_URL = "https://api.openwebninja.com/jsearch/search-v2"


class OpenWebNinjaConnector(BaseJobSource):
    name = "OpenWebNinja"
    requires_api_key = True

    def is_configured(self) -> bool:
        return bool(getattr(settings, "OPENWEBNINJA_KEY", ""))

    def search(
        self,
        keywords: List[str],
        location: Optional[str] = None,
        remote_only: bool = False,
        limit: int = 50,
        date_posted: str = "week",   # today / 3days / week / month
    ) -> List[JobListing]:
        if not self.is_configured():
            logger.warning("OpenWebNinja not configured — set OPENWEBNINJA_KEY in .env")
            return []

        query = " ".join(keywords)
        if location:
            query = f"{query} in {location}"
        elif remote_only:
            query = f"{query} remote"

        headers = {"X-API-Key": settings.OPENWEBNINJA_KEY}

        all_results: List[JobListing] = []
        # Paginate up to 5 pages (10 results each = 50 total)
        pages = max(1, min(5, limit // 10))

        for page in range(1, pages + 1):
            try:
                params = {
                    "query": query,
                    "page": page,
                    "date_posted": date_posted,
                }
                r = requests.get(BASE_URL, params=params, headers=headers, timeout=30)

                if r.status_code == 401:
                    logger.error("OpenWebNinja: Invalid API key")
                    break
                if r.status_code == 429:
                    logger.warning("OpenWebNinja: Rate limit hit")
                    break
                if r.status_code != 200:
                    logger.warning(f"OpenWebNinja: HTTP {r.status_code}")
                    break

                data = r.json()

                # Structure: {"status": "OK", "data": {"jobs": [...]}}
                inner = data.get("data", {})
                if isinstance(inner, dict):
                    jobs = inner.get("jobs", [])
                elif isinstance(inner, list):
                    jobs = inner
                else:
                    jobs = data.get("jobs", data.get("results", []))

                if not jobs:
                    break

                for job in jobs:
                    listing = self._normalize(job)
                    if listing:
                        all_results.append(listing)

                # Stop if fewer results than expected (last page)
                if len(jobs) < 10:
                    break

            except requests.RequestException as e:
                logger.error(f"OpenWebNinja request error: {e}")
                break
            except Exception as e:
                logger.error(f"OpenWebNinja unexpected error: {e}")
                break

        logger.info(f"OpenWebNinja: fetched {len(all_results)} jobs for '{query}'")
        return all_results[:limit]

    def _normalize(self, job: dict) -> Optional[JobListing]:
        try:
            # Field name normalization — the API may use different field names
            title = (
                job.get("job_title") or
                job.get("title") or
                job.get("position") or ""
            ).strip()

            company = (
                job.get("employer_name") or
                job.get("company") or
                job.get("company_name") or ""
            ).strip()

            if not title or not company:
                return None

            # Apply URL — prefer direct, fall back to publisher link
            apply_url = (
                job.get("job_apply_link") or
                job.get("apply_link") or
                job.get("url") or
                job.get("job_url") or ""
            ).strip()

            # If apply_options has a direct link, prefer it
            apply_options = job.get("apply_options") or []
            for opt in apply_options:
                if isinstance(opt, dict) and opt.get("is_direct") and opt.get("apply_link"):
                    apply_url = opt["apply_link"]
                    break

            if not apply_url:
                return None

            # Location — use job_location as primary
            location_str = job.get("job_location") or ""
            city = job.get("job_city") or ""
            state = job.get("job_state") or ""
            country = job.get("job_country") or ""
            if location_str and location_str != "Anywhere":
                location = location_str
            else:
                location = ", ".join(p for p in [city, state, country] if p) or "Remote"

            # Remote
            is_remote = (
                job.get("job_is_remote") or
                job.get("is_remote") or
                "remote" in location.lower() or
                "remote" in title.lower()
            )

            # Employment type
            emp_type = (
                job.get("job_employment_type") or
                job.get("employment_type") or
                job.get("job_type") or
                "Full-time"
            )

            # Salary — use direct fields first, then salary_string
            salary_min = salary_max = None
            currency = job.get("job_salary_currency") or "USD"

            sal_min_raw = job.get("job_min_salary")
            sal_max_raw = job.get("job_max_salary")
            try:
                salary_min = float(sal_min_raw) if sal_min_raw is not None else None
                salary_max = float(sal_max_raw) if sal_max_raw is not None else None
            except (ValueError, TypeError):
                pass

            # Fallback: parse salary string like "95K–125K a year"
            if not salary_min and not salary_max:
                sal_str = str(job.get("job_salary_string") or job.get("salary") or "")
                match = re.search(r"\$?([\d,]+)[kK]?\s*[-–]\s*\$?([\d,]+)[kK]?", sal_str)
                if match:
                    def parse_sal(s):
                        s = s.replace(",", "")
                        v = float(s)
                        return v * 1000 if v < 1000 else v
                    try:
                        salary_min = parse_sal(match.group(1))
                        salary_max = parse_sal(match.group(2))
                    except Exception:
                        pass

            # Date posted
            posted_at = None
            date_raw = (
                job.get("job_posted_at_datetime_utc") or
                job.get("posted_at") or
                job.get("date_posted") or
                job.get("job_posted_at")
            )
            if date_raw:
                try:
                    if isinstance(date_raw, (int, float)):
                        posted_at = datetime.fromtimestamp(date_raw)
                    else:
                        posted_at = datetime.fromisoformat(str(date_raw).replace("Z", "+00:00"))
                except Exception:
                    pass
            else:
                # Try relative time hint
                ts = job.get("job_posted_at_timestamp")
                if ts:
                    try:
                        posted_at = datetime.fromtimestamp(int(ts))
                    except Exception:
                        pass

            # Description
            description = (
                job.get("job_description") or
                job.get("description") or
                f"{title} at {company}"
            )[:5000]

            # Skills
            skills_raw = job.get("job_required_skills") or job.get("skills") or []
            if isinstance(skills_raw, str):
                skills_raw = [s.strip() for s in skills_raw.split(",") if s.strip()]

            # Qualifications / requirements
            highlights = job.get("job_highlights") or {}
            requirements = []
            if isinstance(highlights, dict):
                requirements = highlights.get("Qualifications", [])

            # Source platform
            via = job.get("job_publisher") or job.get("via") or job.get("source") or "OpenWebNinja"
            source_name = f"OWN/{via}" if via and via != "OpenWebNinja" else "OpenWebNinja"

            # Company logo
            logo = (
                job.get("employer_logo") or
                job.get("company_logo") or
                job.get("logo")
            )

            return JobListing(
                title=title,
                company=company,
                company_logo=logo,
                location=location,
                country=country or None,
                city=city or None,
                description=description,
                apply_url=apply_url,
                source=source_name,
                external_id=str(job.get("job_id") or job.get("id") or ""),
                employment_type=emp_type,
                salary_min=salary_min,
                salary_max=salary_max,
                salary_currency=currency,
                is_remote=bool(is_remote),
                is_hybrid="hybrid" in str(emp_type).lower(),
                posted_at=posted_at,
                skills_required=skills_raw[:20] if isinstance(skills_raw, list) else [],
                requirements=requirements[:10] if isinstance(requirements, list) else [],
                industry=job.get("job_industry") or job.get("industry") or "",
            )

        except Exception as e:
            logger.debug(f"OpenWebNinja normalize error: {e} | raw: {str(job)[:200]}")
            return None
