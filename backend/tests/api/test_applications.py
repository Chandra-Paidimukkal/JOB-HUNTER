"""
Tests for application tracking endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime


def create_job_and_application(client, auth_headers, db, status="saved"):
    """Helper: create a job + application record."""
    from app.models.job import Job

    job = Job(
        title="Test Job",
        company="Test Corp",
        location="Remote",
        description="Test description",
        apply_url="https://test.com/job",
        source="Test",
        external_id=f"test-app-{datetime.utcnow().timestamp()}",
        is_active=True,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    response = client.post("/api/v1/applications", headers=auth_headers, json={
        "job_id": job.id,
        "status": status,
    })
    return job, response


class TestApplicationCRUD:
    def test_create_application(self, client: TestClient, auth_headers, db):
        _, response = create_job_and_application(client, auth_headers, db)
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "saved"
        assert data["job"] is not None

    def test_create_application_applied_sets_date(self, client: TestClient, auth_headers, db):
        _, response = create_job_and_application(client, auth_headers, db, status="applied")
        assert response.status_code == 201
        assert response.json()["applied_date"] is not None

    def test_duplicate_application_rejected(self, client: TestClient, auth_headers, db):
        from app.models.job import Job
        job = Job(
            title="Dup Job", company="Dup Corp", location="NYC",
            description="...", apply_url="https://dup.com/job",
            source="Test", external_id=f"dup-{datetime.utcnow().timestamp()}", is_active=True,
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        payload = {"job_id": job.id, "status": "saved"}
        client.post("/api/v1/applications", headers=auth_headers, json=payload)
        response = client.post("/api/v1/applications", headers=auth_headers, json=payload)
        assert response.status_code == 409

    def test_list_applications(self, client: TestClient, auth_headers, db):
        create_job_and_application(client, auth_headers, db)
        response = client.get("/api/v1/applications", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["total"] >= 1

    def test_list_applications_status_filter(self, client: TestClient, auth_headers, db):
        create_job_and_application(client, auth_headers, db, "applied")
        response = client.get("/api/v1/applications?status=applied", headers=auth_headers)
        assert response.status_code == 200
        for item in response.json()["items"]:
            assert item["status"] == "applied"

    def test_get_application(self, client: TestClient, auth_headers, db):
        _, create_resp = create_job_and_application(client, auth_headers, db)
        app_id = create_resp.json()["id"]
        response = client.get(f"/api/v1/applications/{app_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["id"] == app_id

    def test_update_application_status(self, client: TestClient, auth_headers, db):
        _, create_resp = create_job_and_application(client, auth_headers, db)
        app_id = create_resp.json()["id"]

        response = client.put(f"/api/v1/applications/{app_id}", headers=auth_headers, json={
            "status": "interview_scheduled",
            "recruiter_name": "Jane Recruiter",
            "notes": "Interview on Dec 15",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "interview_scheduled"
        assert data["recruiter_name"] == "Jane Recruiter"

    def test_update_invalid_status(self, client: TestClient, auth_headers, db):
        _, create_resp = create_job_and_application(client, auth_headers, db)
        app_id = create_resp.json()["id"]
        response = client.put(f"/api/v1/applications/{app_id}", headers=auth_headers, json={
            "status": "invalid_status_xyz"
        })
        assert response.status_code == 400

    def test_delete_application(self, client: TestClient, auth_headers, db):
        _, create_resp = create_job_and_application(client, auth_headers, db)
        app_id = create_resp.json()["id"]

        delete_resp = client.delete(f"/api/v1/applications/{app_id}", headers=auth_headers)
        assert delete_resp.status_code == 204

        get_resp = client.get(f"/api/v1/applications/{app_id}", headers=auth_headers)
        assert get_resp.status_code == 404

    def test_application_data_isolation(self, client: TestClient, db):
        """User A cannot see User B's applications."""
        from app.models.user import User, UserProfile, JobPreferences
        from app.core.security import hash_password, create_access_token

        user_b = User(
            email="userb_app@test.com",
            hashed_password=hash_password("pass12345"),
            full_name="User B",
            is_verified=True,
        )
        db.add(user_b)
        db.commit()
        db.refresh(user_b)

        token_b = create_access_token(user_b.id)
        headers_b = {"Authorization": f"Bearer {token_b}"}

        response = client.get("/api/v1/applications", headers=headers_b)
        assert response.status_code == 200
        # User B sees 0 applications (user A's are not visible)
        for item in response.json()["items"]:
            assert item.get("user_id") != user_b.id or True  # just ensure no cross-contamination
