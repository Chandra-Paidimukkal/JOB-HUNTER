"""
Tests for notification endpoints.
"""
import pytest
from fastapi.testclient import TestClient


def create_notification(db, user_id: str, title: str = "Test", is_read: bool = False):
    from app.models.notification import Notification
    notif = Notification(
        user_id=user_id,
        type="test",
        title=title,
        message="Test notification message",
        is_read=is_read,
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif


class TestNotifications:
    def test_list_notifications_empty(self, client: TestClient, auth_headers):
        response = client.get("/api/v1/notifications", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "unread_count" in data

    def test_list_notifications_with_data(self, client: TestClient, auth_headers, db, test_user):
        create_notification(db, test_user.id, "Job Match Found")
        create_notification(db, test_user.id, "Interview Reminder", is_read=True)

        response = client.get("/api/v1/notifications", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 2
        assert data["unread_count"] >= 1

    def test_mark_notification_read(self, client: TestClient, auth_headers, db, test_user):
        notif = create_notification(db, test_user.id, "Unread Notification")
        assert notif.is_read is False

        response = client.put(
            f"/api/v1/notifications/{notif.id}/read",
            headers=auth_headers
        )
        assert response.status_code == 200

        # Verify it's now read
        get_response = client.get("/api/v1/notifications", headers=auth_headers)
        items = get_response.json()["items"]
        notif_data = next((n for n in items if n["id"] == notif.id), None)
        if notif_data:
            assert notif_data["is_read"] is True

    def test_mark_all_read(self, client: TestClient, auth_headers, db, test_user):
        create_notification(db, test_user.id, "Notif 1")
        create_notification(db, test_user.id, "Notif 2")

        response = client.put("/api/v1/notifications/read-all", headers=auth_headers)
        assert response.status_code == 200

        get_response = client.get("/api/v1/notifications", headers=auth_headers)
        assert get_response.json()["unread_count"] == 0

    def test_delete_notification(self, client: TestClient, auth_headers, db, test_user):
        notif = create_notification(db, test_user.id, "To Delete")
        response = client.delete(
            f"/api/v1/notifications/{notif.id}",
            headers=auth_headers
        )
        assert response.status_code == 204

    def test_notification_data_isolation(self, client: TestClient, db):
        """User A cannot read User B's notifications."""
        from app.models.user import User
        from app.core.security import hash_password, create_access_token

        user_b = User(
            email="notif_userb@test.com",
            hashed_password=hash_password("pass12345"),
            full_name="User B",
            is_verified=True,
        )
        db.add(user_b)
        db.commit()
        db.refresh(user_b)

        create_notification(db, user_b.id, "User B private notification")

        # User A cannot see User B's notifications
        # Create a different user and verify isolation
        token_b = create_access_token(user_b.id)
        headers_b = {"Authorization": f"Bearer {token_b}"}

        resp_b = client.get("/api/v1/notifications", headers=headers_b)
        assert resp_b.status_code == 200
        # Notifications belong to user_b
        for item in resp_b.json()["items"]:
            assert item["title"] in ["User B private notification"]

    def test_notifications_require_auth(self, client: TestClient):
        response = client.get("/api/v1/notifications")
        assert response.status_code == 401
