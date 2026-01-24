"""
Celery configuration for async task processing.
"""
from celery import Celery
from src.utils.config import get_settings


settings = get_settings()

# Initialize Celery app
celery_app = Celery(
    "docops",
    broker=settings.redis_url,
    backend=settings.redis_url,
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
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)
