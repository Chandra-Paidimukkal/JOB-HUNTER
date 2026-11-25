"""
Tests for profile and preferences endpoints.
"""
import pytest
from fastapi.testclient import TestClient


class TestProfile:
    def test_get_profile(self, client: TestClient, auth_headers, test_user):
        response = client.get("/api/v1/profile", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "profile" in data
        assert "preferences" in data
        assert data["user"]["email"] == test_user.email

    def test_update_profile(self, client: TestClient, auth_headers):
        response = client.put("/api/v1/profile", headers=auth_headers, json={
            "current_title": "Senior Software Engineer",
            "current_company": "Updated Corp",
            "total_experience_years": 7.0,
            "technical_skills": ["Python", "FastAPI", "React", "PostgreSQL"],
        })
        assert response.status_code == 200
        data = response.json()
        assert data["profile"]["current_title"] == "Senior Software Engineer"
        assert "FastAPI" in data["profile"]["technical_skills"]

    def test_update_preferences(self, client: TestClient, auth_headers):
        response = client.put("/api/v1/profile/preferences", headers=auth_headers, json={
            "preferred_titles": ["Software Engineer", "Tech Lead"],
            "remote_ok": True,
            "hybrid_ok": True,
            "expected_salary": 150000,
            "currency": "USD",
        })
        assert response.status_code == 200

    def test_complete_onboarding(self, client: TestClient, auth_headers):
        response = client.post("/api/v1/profile/onboarding", headers=auth_headers, json={
            "personal": {
                "full_name": "John Updated",
                "phone": "+1 555 000 1234",
                "current_location": "San Francisco, CA",
                "linkedin_url": "https://linkedin.com/in/john",
            },
            "professional": {
                "current_title": "Staff Engineer",
                "total_experience_years": 8,
                "technical_skills": ["Python", "Go", "Kubernetes"],
                "soft_skills": ["Mentoring", "Leadership"],
            },
            "preferences": {
                "remote_ok": True,
                "expected_salary": 200000,
                "full_time": True,
            },
            "objective": {
                "career_objective": "Build impactful distributed systems",
                "short_term_goals": "Lead platform team",
                "long_term_goals": "VP Engineering",
            },
        })
        assert response.status_code == 200
        assert "completed" in response.json()["message"].lower()

    def test_profile_requires_auth(self, client: TestClient):
        response = client.get("/api/v1/profile")
        assert response.status_code == 401

    def test_data_isolation(self, client: TestClient, db):
        """Users cannot access each other's profiles."""
        from app.models.user import User, UserProfile, JobPreferences
        from app.core.security import hash_password, create_access_token

        user2 = User(
            email="user2@test.com",
            hashed_password=hash_password("password123"),
            full_name="User Two",
            is_verified=True,
        )
        db.add(user2)
        db.commit()
        db.refresh(user2)

        token2 = create_access_token(user2.id)
        headers2 = {"Authorization": f"Bearer {token2}"}

        # user2 gets THEIR profile, not user1's
        response = client.get("/api/v1/profile", headers=headers2)
        assert response.status_code == 200
        assert response.json()["user"]["email"] == "user2@test.com"
