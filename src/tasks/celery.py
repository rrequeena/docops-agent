"""
Celery configuration for async task processing.
"""
from celery import Celery
from celery.schedules import crontab


def get_settings():
    """Lazy import to avoid validation errors at import time."""
    from src.utils.config import get_settings as _get_settings
    return _get_settings()


try:
    settings = get_settings()
    redis_url = settings.redis_url
except Exception:
    redis_url = "redis://localhost:6379/0"

# Initialize Celery app
celery_app = Celery(
    "docops",
    broker=redis_url,
    backend=redis_url,
    include=[
        "src.tasks.process",
        "src.tasks.analyze",
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    result_expires=3600,
    result_persistent=True,
    broker_connection_retry_on_startup=True,
)

# Periodic tasks
celery_app.conf.beat_schedule = {
    "cleanup-old-results": {
        "task": "cleanup_document",
        "schedule": crontab(hour=2, minute=0),
    },
}
