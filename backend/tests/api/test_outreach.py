"""
Tests for outreach CRM endpoints.
"""
import pytest
from fastapi.testclient import TestClient


class TestOutreach:
    def test_create_outreach_contact(self, client: TestClient, auth_headers):
        response = client.post("/api/v1/outreach", headers=auth_headers, json={
            "company_name": "Google",
            "company_website": "https://google.com",
            "company_industry": "Technology",
            "contact_name": "Jane Smith",
            "contact_designation": "Engineering Manager",
            "contact_email": "jane@google.com",
            "email_type": "hr_outreach",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["company_name"] == "Google"
        assert data["status"] == "new_prospect"

    def test_list_outreach(self, client: TestClient, auth_headers):
        response = client.get("/api/v1/outreach", headers=auth_headers)
        assert response.status_code == 200
        assert "items" in response.json()

    def test_update_outreach_status(self, client: TestClient, auth_headers):
        create_resp = client.post("/api/v1/outreach", headers=auth_headers, json={
            "company_name": "Stripe",
        })
        contact_id = create_resp.json()["id"]

        response = client.put(f"/api/v1/outreach/{contact_id}", headers=auth_headers, json={
            "status": "sent",
            "email_subject": "Job Inquiry",
            "generated_email": "Dear Hiring Team...",
        })
        assert response.status_code == 200
        assert response.json()["status"] == "sent"

    def test_delete_outreach(self, client: TestClient, auth_headers):
        create_resp = client.post("/api/v1/outreach", headers=auth_headers, json={
            "company_name": "ToDelete Corp",
        })
        contact_id = create_resp.json()["id"]
        delete_resp = client.delete(f"/api/v1/outreach/{contact_id}", headers=auth_headers)
        assert delete_resp.status_code == 204

    def test_get_nonexistent_outreach(self, client: TestClient, auth_headers):
        response = client.get(
            "/api/v1/outreach/00000000-0000-0000-0000-000000000000",
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_outreach_requires_auth(self, client: TestClient):
        response = client.get("/api/v1/outreach")
        assert response.status_code == 401


class TestEmailStatus:
    def test_email_status_not_connected(self, client: TestClient, auth_headers):
        response = client.get("/api/v1/email/status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "connected" in data
        # Without OAuth configured, should be not connected
        assert data["connected"] is False
