from celery import Celery
from celery.schedules import crontab

from app.core.config import settings
from app.core.logging import logger

if settings.REDIS_PASSWORD and settings.REDIS_USERNAME:
    REDIS_URL = (
        f"redis://{settings.REDIS_USERNAME}:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/0"
    )
elif settings.REDIS_PASSWORD:
    REDIS_URL = (
        f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/0"
    )
else:
    REDIS_URL = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0"

logger.info(f"Starting Celery with Redis URL: {REDIS_URL}")

celery_app = Celery("app")
celery_app.conf.update(
    broker_url=REDIS_URL,
    result_backend=REDIS_URL,
    task_serializer="json",
    accept_content=["json"],
    timezone=settings.TIMEZONE_NAME,
    enable_utc=True,
    include=["app.tasks"],
)

celery_app.conf.beat_schedule = {
    "health-check": {
        "task": "app.tasks.health_check",
        "schedule": crontab(minute="*/1"),
    },
    "sync-up-in-progress-orders": {
        "task": "app.tasks.order.sync_up_in_progress_orders_task",
        "schedule": crontab(minute="*/1"),
    },
    "sync-up-timeout-payments": {
        "task": "app.tasks.payment.sync_up_timeout_payments_task",
        "schedule": crontab(minute="*/1"),
    },
    "sync-up-promotion-campaigns": {
        "task": "app.tasks.promotion.sync_up_promotion_campaign_task",
        "schedule": crontab(minute="*/1"),
    },
    "reset-no-responding-machines": {
        "task": "app.tasks.machine.reset_no_responding_machines_task",
        "schedule": crontab(minute="*/5"),
    },
}
