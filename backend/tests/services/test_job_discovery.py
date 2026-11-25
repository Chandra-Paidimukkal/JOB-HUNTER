"""
Tests for job discovery service and connectors.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


class TestJobConnectors:
    def test_remotive_connector_configured(self):
        from app.integrations.job_sources.remotive import RemotiveConnector
        connector = RemotiveConnector()
        assert connector.is_configured() is True
        assert connector.requires_api_key is False

    def test_adzuna_connector_not_configured_without_keys(self):
        from app.integrations.job_sources.adzuna import AdzunaConnector
        from app.core.config import settings

        connector = AdzunaConnector()
        # Without keys set it should return not configured
        original_id = settings.ADZUNA_APP_ID
        original_key = settings.ADZUNA_API_KEY
        settings.ADZUNA_APP_ID = ""
        settings.ADZUNA_API_KEY = ""
        assert connector.is_configured() is False
        settings.ADZUNA_APP_ID = original_id
        settings.ADZUNA_API_KEY = original_key

    def test_jsearch_connector_not_configured_without_key(self):
        from app.integrations.job_sources.jsearch import JSearchConnector
        from app.core.config import settings

        connector = JSearchConnector()
        original = settings.JSEARCH_API_KEY
        settings.JSEARCH_API_KEY = ""
        assert connector.is_configured() is False
        settings.JSEARCH_API_KEY = original

    def test_remotive_returns_empty_on_api_failure(self):
        from app.integrations.job_sources.remotive import RemotiveConnector
        import requests
        connector = RemotiveConnector()

        with patch("requests.get") as mock_get:
            mock_get.side_effect = requests.RequestException("Network error")
            results = connector.search(keywords=["python"])
            assert results == []

    def test_adzuna_returns_empty_when_not_configured(self):
        from app.integrations.job_sources.adzuna import AdzunaConnector
        from app.core.config import settings

        connector = AdzunaConnector()
        settings.ADZUNA_APP_ID = ""
        settings.ADZUNA_API_KEY = ""
        results = connector.search(keywords=["python"])
        assert results == []

    def test_remotive_normalizes_listing(self):
        from app.integrations.job_sources.remotive import RemotiveConnector

        connector = RemotiveConnector()
        raw = {
            "id": 12345,
            "title": "Senior Python Developer",
            "company_name": "Remote Corp",
            "company_logo_url": "https://logo.example.com/logo.png",
            "candidate_required_location": "Worldwide",
            "description": "<p>Python developer needed</p>",
            "url": "https://remotive.com/job/12345",
            "job_type": "full_time",
            "category": "Software Development",
            "tags": ["python", "django", "postgresql"],
            "publication_date": "2026-11-01T10:00:00Z",
        }
        listing = connector._normalize(raw)
        assert listing.title == "Senior Python Developer"
        assert listing.company == "Remote Corp"
        assert listing.is_remote is True
        assert "python" in listing.skills_required
        assert listing.source == "Remotive"

    def test_jsearch_normalizes_listing(self):
        from app.integrations.job_sources.jsearch import JSearchConnector

        connector = JSearchConnector()
        raw = {
            "job_id": "js_001",
            "job_title": "Full Stack Developer",
            "employer_name": "Tech Co",
            "employer_logo": None,
            "job_city": "San Francisco",
            "job_country": "US",
            "job_description": "Build scalable web apps",
            "job_apply_link": "https://techco.com/jobs/1",
            "job_employment_type": "FULLTIME",
            "job_min_salary": 120000,
            "job_max_salary": 180000,
            "job_salary_currency": "USD",
            "job_is_remote": False,
            "job_posted_at_timestamp": "1700000000",
            "job_required_skills": ["React", "Node.js"],
            "job_highlights": {"Qualifications": ["5+ years experience"]},
        }
        listing = connector._normalize(raw)
        assert listing.title == "Full Stack Developer"
        assert listing.salary_min == 120000
        assert listing.salary_max == 180000
        assert "React" in listing.skills_required
        assert listing.source == "JSearch"


class TestDeduplication:
    def test_fingerprint_consistency(self):
        from app.services.jobs.discovery_service import compute_job_fingerprint
        from app.integrations.job_sources.base import JobListing

        listing = JobListing(
            title="Python Engineer",
            company="Acme",
            location="Remote",
            description="...",
            apply_url="https://acme.com/jobs/python",
            source="Remotive",
        )
        fp1 = compute_job_fingerprint(listing)
        fp2 = compute_job_fingerprint(listing)
        assert fp1 == fp2  # Deterministic

    def test_different_listings_different_fingerprints(self):
        from app.services.jobs.discovery_service import compute_job_fingerprint
        from app.integrations.job_sources.base import JobListing

        listing1 = JobListing(
            title="Python Engineer", company="Acme", location="Remote",
            description="...", apply_url="https://acme.com/job/1", source="Remotive"
        )
        listing2 = JobListing(
            title="React Developer", company="Acme", location="Remote",
            description="...", apply_url="https://acme.com/job/2", source="Remotive"
        )
        assert compute_job_fingerprint(listing1) != compute_job_fingerprint(listing2)

    def test_same_url_same_fingerprint_different_sources(self):
        from app.services.jobs.discovery_service import compute_job_fingerprint
        from app.integrations.job_sources.base import JobListing

        listing1 = JobListing(
            title="Engineer", company="Corp", location="NYC",
            description="...", apply_url="https://corp.com/job/1", source="Adzuna"
        )
        listing2 = JobListing(
            title="Engineer", company="Corp", location="NYC",
            description="Different description", apply_url="https://corp.com/job/1", source="JSearch"
        )
        # Same title + company + URL = same fingerprint regardless of source
        assert compute_job_fingerprint(listing1) == compute_job_fingerprint(listing2)
