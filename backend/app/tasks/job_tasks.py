"""
Background job discovery tasks.
"""
import logging
from app.tasks.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.user import User
from app.services.jobs.discovery_service import run_job_discovery

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def trigger_job_discovery_for_user(self, user_id: str, keywords=None, location=None):
    """Trigger job discovery for a single user."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user:
            return {"status": "skipped", "reason": "User not found"}

        result = run_job_discovery(db=db, user=user, keywords=keywords, location=location)
        logger.info(f"Discovery for user {user_id}: {result}")
        return {"status": "completed", **result}
    except Exception as exc:
        logger.error(f"Discovery failed for user {user_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()


@celery_app.task
def run_all_users_discovery():
    """Scheduled: run job discovery for all active users."""
    db = SessionLocal()
    try:
        users = db.query(User).filter(User.is_active == True, User.onboarding_completed == True).all()
        for user in users:
            trigger_job_discovery_for_user.delay(user.id)
        return {"triggered_for": len(users)}
    finally:
        db.close()
