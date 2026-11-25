"""
Tests for authentication endpoints.
"""
import pytest
from fastapi.testclient import TestClient


class TestRegister:
    def test_register_success(self, client: TestClient):
        response = client.post("/api/v1/auth/register", json={
            "email": "newuser@test.com",
            "password": "securepass123",
            "full_name": "New User",
        })
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "newuser@test.com"
        assert data["user"]["onboarding_completed"] is False

    def test_register_duplicate_email(self, client: TestClient):
        payload = {"email": "dup@test.com", "password": "pass12345", "full_name": "Dup"}
        client.post("/api/v1/auth/register", json=payload)
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    def test_register_weak_password(self, client: TestClient):
        response = client.post("/api/v1/auth/register", json={
            "email": "weak@test.com",
            "password": "123",
            "full_name": "Weak",
        })
        assert response.status_code == 422

    def test_register_invalid_email(self, client: TestClient):
        response = client.post("/api/v1/auth/register", json={
            "email": "not-an-email",
            "password": "pass12345",
            "full_name": "Bad Email",
        })
        assert response.status_code == 422


class TestLogin:
    def test_login_success(self, client: TestClient, test_user):
        response = client.post("/api/v1/auth/login", json={
            "email": "test@jobhunter.ai",
            "password": "testpassword123",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "test@jobhunter.ai"

    def test_login_wrong_password(self, client: TestClient, test_user):
        response = client.post("/api/v1/auth/login", json={
            "email": "test@jobhunter.ai",
            "password": "wrongpassword",
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client: TestClient):
        response = client.post("/api/v1/auth/login", json={
            "email": "ghost@test.com",
            "password": "pass12345",
        })
        assert response.status_code == 401

    def test_login_invalid_email_format(self, client: TestClient):
        response = client.post("/api/v1/auth/login", json={
            "email": "not-email",
            "password": "pass12345",
        })
        assert response.status_code == 422


class TestProtectedRoutes:
    def test_get_me_authenticated(self, client: TestClient, auth_headers, test_user):
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["email"] == test_user.email

    def test_get_me_no_token(self, client: TestClient):
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_get_me_invalid_token(self, client: TestClient):
        response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
        assert response.status_code == 401

    def test_logout(self, client: TestClient, auth_headers):
        response = client.post("/api/v1/auth/logout", headers=auth_headers)
        assert response.status_code == 200


class TestPasswordReset:
    def test_forgot_password_always_200(self, client: TestClient):
        """Should always return 200 to prevent email enumeration."""
        response = client.post("/api/v1/auth/forgot-password", json={
            "email": "doesnotexist@test.com"
        })
        assert response.status_code == 200
        assert "sent" in response.json()["message"].lower()

    def test_reset_password_invalid_token(self, client: TestClient):
        response = client.post("/api/v1/auth/reset-password", json={
            "token": "invalid-token",
            "password": "newpassword123",
        })
        assert response.status_code == 400
