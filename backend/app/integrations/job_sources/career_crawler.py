"""
Company Career Page Crawler
Discovers job listings directly from any company's careers page.
Uses sitemap detection + common ATS patterns + Playwright fallback.
"""
import logging
import requests
import re
from typing import List, Optional
from datetime import datetime
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from app.integrations.job_sources.base import BaseJobSource, JobListing

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Common career page URL patterns
CAREER_URL_PATTERNS = [
    "/careers", "/jobs", "/careers/", "/jobs/", "/join-us", "/work-with-us",
    "/about/careers", "/company/careers", "/en/careers",
]

# ATS platform detection patterns
ATS_PATTERNS = {
    "greenhouse": re.compile(r"boards\.greenhouse\.io/([\w-]+)|greenhouse\.io/([\w-]+)", re.I),
    "lever": re.compile(r"jobs\.lever\.co/([\w-]+)|lever\.co/([\w-]+)", re.I),
    "ashby": re.compile(r"jobs\.ashbyhq\.com/([\w-]+)", re.I),
    "workable": re.compile(r"(\w+)\.workable\.com", re.I),
    "recruitee": re.compile(r"(\w+)\.recruitee\.com", re.I),
    "bamboohr": re.compile(r"(\w+)\.bamboohr\.com/careers", re.I),
    "smartrecruiters": re.compile(r"careers\.smartrecruiters\.com/([\w-]+)", re.I),
    "workday": re.compile(r"(\w+)\.wd\d+\.myworkdayjobs\.com", re.I),
}


class CareerPageCrawler(BaseJobSource):
    """Crawls a company's career page to find open positions."""

    name = "Company Careers"
    requires_api_key = False

    def __init__(self, company_name: str = None, website: str = None):
        self.company_name = company_name
        self.website = website

    def is_configured(self) -> bool:
        return True

    def search(
        self,
        keywords: List[str],
        location: Optional[str] = None,
        remote_only: bool = False,
        limit: int = 30,
    ) -> List[JobListing]:
        """Search on a specific company's career page."""
        if not self.website:
            return []
        return self.crawl_company(self.website, self.company_name or "Unknown", keywords, limit)

    # ── Public API for single company crawl ──────────────────────
    def crawl_company(self, website: str, company_name: str, keywords: List[str], limit: int = 30) -> List[JobListing]:
        """Crawl a single company's career page for job listings."""
        results = []

        if not website.startswith("http"):
            website = f"https://{website}"

        try:
            # 1. First try known ATS APIs directly
            ats_jobs = self._try_ats_apis(website, company_name, keywords)
            if ats_jobs:
                return ats_jobs[:limit]

            # 2. Try common career URL patterns
            for path in CAREER_URL_PATTERNS:
                careers_url = urljoin(website, path)
                jobs = self._scrape_career_page(careers_url, company_name, keywords)
                if jobs:
                    results.extend(jobs)
                    if len(results) >= limit:
                        break

            # 3. Find career link from homepage
            if len(results) < limit:
                careers_url = self._find_careers_link(website)
                if careers_url:
                    jobs = self._scrape_career_page(careers_url, company_name, keywords)
                    results.extend(jobs)

        except Exception as e:
            logger.error(f"Career crawl error for {company_name}: {e}")

        # Dedup by URL
        seen = set()
        deduped = []
        for job in results:
            if job.apply_url not in seen:
                seen.add(job.apply_url)
                deduped.append(job)

        logger.info(f"Career crawl {company_name}: found {len(deduped)} jobs")
        return deduped[:limit]

    def _try_ats_apis(self, website: str, company_name: str, keywords: List[str]) -> List[JobListing]:
        """If the company uses a known ATS, query its API directly."""
        results = []

        try:
            r = requests.get(website, headers=HEADERS, timeout=10, allow_redirects=True)
            html = r.text

            # Check which ATS they use
            for ats_name, pattern in ATS_PATTERNS.items():
                match = pattern.search(html)
                if not match:
                    continue

                slug = next(g for g in match.groups() if g)
                if not slug:
                    continue

                if ats_name == "greenhouse":
                    results = self._fetch_greenhouse(slug, company_name)
                elif ats_name == "lever":
                    results = self._fetch_lever(slug, company_name)
                elif ats_name == "ashby":
                    results = self._fetch_ashby(slug, company_name)
                elif ats_name == "workable":
                    results = self._fetch_workable(slug, company_name)
                elif ats_name == "smartrecruiters":
                    results = self._fetch_smartrecruiters(slug, company_name)

                if results:
                    break

        except Exception as e:
            logger.debug(f"ATS detection error: {e}")

        # Filter by keywords
        if keywords and results:
            keyword_set = {k.lower() for k in keywords}
            results = [
                job for job in results
                if any(kw in job.title.lower() for kw in keyword_set)
                or not keyword_set
            ] or results[:10]  # If no keyword matches, return top 10 anyway

        return results

    def _fetch_greenhouse(self, slug, company_name):
        try:
            r = requests.get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs", timeout=10)
            if r.status_code != 200:
                return []
            return [
                JobListing(
                    title=job.get("title", ""),
                    company=company_name,
                    location=job.get("location", {}).get("name", ""),
                    description=f"Position at {company_name}. Apply via link.",
                    apply_url=job.get("absolute_url", ""),
                    source="Company Careers",
                    external_id=str(job.get("id", "")),
                    employment_type="Full-time",
                )
                for job in r.json().get("jobs", [])
                if job.get("title")
            ]
        except Exception:
            return []

    def _fetch_lever(self, slug, company_name):
        try:
            r = requests.get(f"https://api.lever.co/v0/postings/{slug}?mode=json", timeout=10)
            if r.status_code != 200:
                return []
            return [
                JobListing(
                    title=job.get("text", ""),
                    company=company_name,
                    location=job.get("categories", {}).get("location", ""),
                    description=f"Position at {company_name}. Apply via link.",
                    apply_url=job.get("hostedUrl", ""),
                    source="Company Careers",
                    external_id=job.get("id", ""),
                )
                for job in r.json()
                if job.get("text")
            ]
        except Exception:
            return []

    def _fetch_ashby(self, slug, company_name):
        try:
            r = requests.post(
                f"https://api.ashbyhq.com/posting-api/job-board/{slug}",
                json={"limit": 50},
                timeout=10,
            )
            if r.status_code != 200:
                return []
            return [
                JobListing(
                    title=job.get("title", ""),
                    company=company_name,
                    location=job.get("location", ""),
                    description=job.get("descriptionPlainText", "")[:3000],
                    apply_url=job.get("jobUrl") or job.get("applyUrl", ""),
                    source="Company Careers",
                    external_id=job.get("id", ""),
                    employment_type=job.get("employmentType", "Full-time"),
                )
                for job in r.json().get("jobs", [])
                if job.get("title")
            ]
        except Exception:
            return []

    def _fetch_workable(self, slug, company_name):
        try:
            r = requests.get(f"https://{slug}.workable.com/api/v3/jobs", timeout=10)
            if r.status_code != 200:
                return []
            return [
                JobListing(
                    title=job.get("title", ""),
                    company=company_name,
                    location=job.get("location", {}).get("city", ""),
                    description=job.get("description", "")[:3000],
                    apply_url=job.get("shortlink") or job.get("apply_url", ""),
                    source="Company Careers",
                    external_id=job.get("id", ""),
                    employment_type=job.get("type", "Full-time"),
                )
                for job in r.json().get("jobs", [])
                if job.get("title")
            ]
        except Exception:
            return []

    def _fetch_smartrecruiters(self, slug, company_name):
        try:
            r = requests.get(
                f"https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=50",
                timeout=10,
            )
            if r.status_code != 200:
                return []
            return [
                JobListing(
                    title=job.get("name", ""),
                    company=company_name,
                    location=job.get("location", {}).get("city", ""),
                    description=f"Position at {company_name}. Apply via link.",
                    apply_url=f"https://jobs.smartrecruiters.com/{slug}/{job.get('id', '')}",
                    source="Company Careers",
                    external_id=job.get("id", ""),
                    employment_type=job.get("typeOfEmployment", {}).get("label", "Full-time"),
                )
                for job in r.json().get("content", [])
                if job.get("name")
            ]
        except Exception:
            return []

    def _scrape_career_page(self, url: str, company_name: str, keywords: List[str]) -> List[JobListing]:
        """Scrape a career page for job listings."""
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code != 200:
                return []

            soup = BeautifulSoup(r.text, "html.parser")
            results = []
            keyword_set = {k.lower() for k in keywords} if keywords else None

            # Common job listing selectors
            selectors = [
                "a[href*='job']", "a[href*='position']", "a[href*='/careers/']",
                ".job-listing a", ".job-item a", ".position a", ".opening a",
                "[data-job-title]", ".job-card a", ".careers-job-link",
                "a.job-link", ".vacancy a", ".role a",
            ]

            seen_titles = set()
            for sel in selectors:
                for link in soup.select(sel):
                    try:
                        title_el = link if link.get_text(strip=True) else link.find(["h2", "h3", "h4", "span"])
                        title = (title_el.get_text(strip=True) if title_el else "").strip()

                        if not title or len(title) < 4 or title.lower() in seen_titles:
                            continue
                        # Filter out nav links
                        if title.lower() in ("jobs", "careers", "apply", "view all", "see all", "search"):
                            continue

                        seen_titles.add(title.lower())

                        # Keyword filter
                        if keyword_set and not any(kw in title.lower() for kw in keyword_set):
                            continue

                        href = link.get("href", "")
                        apply_url = urljoin(url, href) if href else url

                        # Extract location if nearby
                        parent = link.find_parent(["div", "li", "article"])
                        location = ""
                        if parent:
                            loc_el = parent.select_one(".location, .job-location, [class*='location'], [class*='Location']")
                            if loc_el:
                                location = loc_el.get_text(strip=True)

                        results.append(JobListing(
                            title=title,
                            company=company_name,
                            location=location or "See posting",
                            description=f"{title} position at {company_name}. View and apply via the link.",
                            apply_url=apply_url,
                            source="Company Careers",
                            employment_type="Full-time",
                        ))

                        if len(results) >= 50:
                            return results

                    except Exception:
                        continue

                if results:
                    break

            return results
        except Exception as e:
            logger.debug(f"Career page scrape error {url}: {e}")
            return []

    def _find_careers_link(self, website: str) -> Optional[str]:
        """Find the careers page link from the company homepage."""
        try:
            r = requests.get(website, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")

            # Look for career-related links
            for link in soup.find_all("a", href=True):
                text = link.get_text(strip=True).lower()
                href = link["href"].lower()
                if any(kw in text or kw in href for kw in ("career", "jobs", "join us", "work with us", "openings", "vacancies")):
                    return urljoin(website, link["href"])
        except Exception:
            pass
        return None
