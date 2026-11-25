"""
Tests for analytics endpoints.
"""
import pytest
from fastapi.testclient import TestClient


class TestAnalytics:
    def test_overview(self, client: TestClient, auth_headers):
        response = client.get("/api/v1/analytics/overview", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        expected_keys = [
            "total_jobs_discovered", "high_match_jobs", "saved_jobs",
            "applications_submitted", "emails_generated", "outreach_sent",
            "recruiter_responses", "interviews_scheduled", "offers_received",
        ]
        for key in expected_keys:
            assert key in data, f"Missing key: {key}"
            assert isinstance(data[key], int)

    def test_overview_all_zeros_for_new_user(self, client: TestClient, db):
        """A brand new user should see all zeros."""
        from app.models.user import User
        from app.core.security import hash_password, create_access_token

        fresh_user = User(
            email="fresh_analytics@test.com",
            hashed_password=hash_password("pass12345"),
            full_name="Fresh User",
            is_verified=True,
        )
        db.add(fresh_user)
        db.commit()
        db.refresh(fresh_user)

        token = create_access_token(fresh_user.id)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/analytics/overview", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["applications_submitted"] == 0
        assert data["outreach_sent"] == 0
        assert data["offers_received"] == 0

    def test_applications_analytics(self, client: TestClient, auth_headers):
        response = client.get("/api/v1/analytics/applications", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "status_breakdown" in data
        assert "daily_applications" in data
        assert "top_companies" in data

    def test_outreach_analytics(self, client: TestClient, auth_headers):
        response = client.get("/api/v1/analytics/outreach", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "emails_sent" in data
        assert "response_rate" in data

    def test_job_matches_analytics(self, client: TestClient, auth_headers):
        response = client.get("/api/v1/analytics/job-matches", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "by_category" in data
        assert "average_match_score" in data

    def test_analytics_requires_auth(self, client: TestClient):
        response = client.get("/api/v1/analytics/overview")
        assert response.status_code == 401
