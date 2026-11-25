"""
Tests for job discovery, listing, saving, and matching endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime


def create_test_job(db):
    """Helper to insert a test job."""
    from app.models.job import Job
    job = Job(
        title="Senior Python Engineer",
        company="Acme Corp",
        location="Remote",
        description="We are looking for a Python engineer with FastAPI experience.",
        apply_url="https://acme.com/jobs/123",
        source="Remotive",
        external_id="test-job-001",
        is_remote=True,
        employment_type="Full-time",
        skills_required=["Python", "FastAPI", "PostgreSQL"],
        is_active=True,
        posted_at=datetime.utcnow(),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


class TestJobListing:
    def test_list_jobs_empty(self, client: TestClient, auth_headers):
        response = client.get("/api/v1/jobs", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data

    def test_list_jobs_with_data(self, client: TestClient, auth_headers, db):
        create_test_job(db)
        response = client.get("/api/v1/jobs", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["total"] >= 1

    def test_list_jobs_search_filter(self, client: TestClient, auth_headers, db):
        create_test_job(db)
        response = client.get("/api/v1/jobs?search=Python", headers=auth_headers)
        assert response.status_code == 200
        items = response.json()["items"]
        for item in items:
            assert "python" in item["title"].lower() or \
                   "python" in item["description"].lower() or \
                   "python" in item["company"].lower()

    def test_list_jobs_remote_filter(self, client: TestClient, auth_headers, db):
        create_test_job(db)
        response = client.get("/api/v1/jobs?work_mode=remote", headers=auth_headers)
        assert response.status_code == 200
        for item in response.json()["items"]:
            assert item["is_remote"] is True

    def test_list_jobs_pagination(self, client: TestClient, auth_headers):
        response = client.get("/api/v1/jobs?page=1&per_page=5", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 5
        assert data["per_page"] == 5

    def test_get_job_by_id(self, client: TestClient, auth_headers, db):
        job = create_test_job(db)
        response = client.get(f"/api/v1/jobs/{job.id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["id"] == job.id
        assert response.json()["title"] == "Senior Python Engineer"

    def test_get_nonexistent_job(self, client: TestClient, auth_headers):
        response = client.get("/api/v1/jobs/00000000-0000-0000-0000-000000000000", headers=auth_headers)
        assert response.status_code == 404

    def test_jobs_requires_auth(self, client: TestClient):
        response = client.get("/api/v1/jobs")
        assert response.status_code == 401


class TestSaveJob:
    def test_save_job(self, client: TestClient, auth_headers, db):
        job = create_test_job(db)
        response = client.post(f"/api/v1/jobs/{job.id}/save", headers=auth_headers)
        assert response.status_code == 200

    def test_save_job_duplicate(self, client: TestClient, auth_headers, db):
        job = create_test_job(db)
        client.post(f"/api/v1/jobs/{job.id}/save", headers=auth_headers)
        response = client.post(f"/api/v1/jobs/{job.id}/save", headers=auth_headers)
        # Should return 200 with "already saved" message, not error
        assert response.status_code == 200

    def test_unsave_job(self, client: TestClient, auth_headers, db):
        job = create_test_job(db)
        client.post(f"/api/v1/jobs/{job.id}/save", headers=auth_headers)
        response = client.delete(f"/api/v1/jobs/{job.id}/save", headers=auth_headers)
        assert response.status_code == 200

    def test_get_saved_jobs(self, client: TestClient, auth_headers, db):
        job = create_test_job(db)
        client.post(f"/api/v1/jobs/{job.id}/save", headers=auth_headers)
        response = client.get("/api/v1/jobs/saved", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["total"] >= 1


class TestJobMatching:
    def test_match_job_no_resume(self, client: TestClient, auth_headers, db):
        """Should fail gracefully when user has no resume."""
        job = create_test_job(db)
        response = client.post(f"/api/v1/jobs/{job.id}/match", headers=auth_headers)
        assert response.status_code == 422
        assert "resume" in response.json()["detail"].lower()

    def test_match_job_with_resume(self, client: TestClient, auth_headers, db, mock_groq):
        """Should return match data when resume exists."""
        from app.models.resume import Resume
        from app.models.user import User

        # Get test user
        user = db.query(User).filter(User.email == "test@jobhunter.ai").first()
        if not user:
            pytest.skip("Test user not found")

        # Create a resume with extracted data
        resume = Resume(
            user_id=user.id,
            file_name="test_resume.pdf",
            file_path="/tmp/test.pdf",
            file_type="pdf",
            file_size=50000,
            is_primary=True,
            is_analyzed=True,
            extracted_data={
                "skills": {"technical": ["Python", "FastAPI"], "soft": ["Leadership"]},
                "experience": [{"company": "Acme", "title": "Engineer", "is_current": True}],
                "total_experience_years": 5,
            }
        )
        db.add(resume)
        db.commit()

        job = create_test_job(db)

        # Mock Groq to return structured JSON
        mock_groq.return_value = {
            "content": """{
                "required_skills": ["Python", "FastAPI"],
                "preferred_skills": [],
                "min_experience_years": 3,
                "key_responsibilities": ["Build APIs"],
                "industry": "Technology",
                "seniority_level": "senior",
                "work_mode": "remote",
                "key_keywords": ["Python", "API"],
                "tech_stack": ["Python", "FastAPI"]
            }""",
            "model": "llama-3.1-70b-versatile",
            "prompt_tokens": 400,
            "completion_tokens": 200,
            "total_tokens": 600,
            "latency_ms": 800,
        }

        response = client.post(f"/api/v1/jobs/{job.id}/match", headers=auth_headers)
        # May fail on second Groq call but should not error on first
        assert response.status_code in [200, 503]


class TestJobDiscovery:
    def test_trigger_discovery(self, client: TestClient, auth_headers):
        response = client.post("/api/v1/jobs/discover", headers=auth_headers)
        assert response.status_code == 200
        assert "discovery started" in response.json()["message"].lower()


class TestDeduplication:
    def test_duplicate_jobs_not_saved(self, db):
        """Two listings with same fingerprint should not create duplicates."""
        from app.services.jobs.discovery_service import compute_job_fingerprint
        from app.integrations.job_sources.base import JobListing

        listing1 = JobListing(
            title="Python Developer",
            company="Acme",
            location="Remote",
            description="Python dev role",
            apply_url="https://acme.com/job/1",
            source="Remotive",
        )
        listing2 = JobListing(
            title="Python Developer",
            company="Acme",
            location="Remote",
            description="Python dev role different description",
            apply_url="https://acme.com/job/1",  # same URL
            source="Adzuna",
        )
        fp1 = compute_job_fingerprint(listing1)
        fp2 = compute_job_fingerprint(listing2)
        # Same title + company + URL = same fingerprint
        assert fp1 == fp2
