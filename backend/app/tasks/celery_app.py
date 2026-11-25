"""
Celery background task configuration.
Requires Redis running on REDIS_URL.
"""
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "jobhunter",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.job_tasks", "app.tasks.notification_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# Scheduled tasks
celery_app.conf.beat_schedule = {
    # Discover new jobs every 6 hours
    "discover-jobs-every-6h": {
        "task": "app.tasks.job_tasks.run_all_users_discovery",
        "schedule": crontab(minute=0, hour="*/6"),
    },
    # Send follow-up reminders daily at 9am UTC
    "followup-reminders-daily": {
        "task": "app.tasks.notification_tasks.send_followup_reminders",
        "schedule": crontab(minute=0, hour=9),
    },
}
