"""
Notification and follow-up reminder tasks.
"""
import logging
from datetime import datetime, timedelta
from app.tasks.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.followup import FollowupTask
from app.models.notification import Notification

logger = logging.getLogger(__name__)


@celery_app.task
def send_followup_reminders():
    """Check for follow-up tasks due today and create notifications."""
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        tomorrow = now + timedelta(days=1)

        due_tasks = (
            db.query(FollowupTask)
            .filter(
                FollowupTask.is_completed == False,
                FollowupTask.due_date <= tomorrow,
                FollowupTask.reminder_sent == False,
            )
            .all()
        )

        for task in due_tasks:
            notif = Notification(
                user_id=task.user_id,
                type="followup_reminder",
                title="Follow-up Due",
                message=f"You have a follow-up task due: {task.title}",
                is_read=False,
                link=f"/{task.related_type}s",
            )
            db.add(notif)
            task.reminder_sent = True

        db.commit()
        logger.info(f"Sent {len(due_tasks)} follow-up reminders")
        return {"reminders_sent": len(due_tasks)}
    finally:
        db.close()


@celery_app.task
def create_notification(user_id: str, type: str, title: str, message: str, link: str = None):
    """Create a notification for a user."""
    db = SessionLocal()
    try:
        notif = Notification(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            link=link,
            is_read=False,
        )
        db.add(notif)
        db.commit()
    finally:
        db.close()
