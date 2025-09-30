from app.core.celery_app import celery_app
from app.core.logging import logger


@celery_app.task(name="app.tasks.health_check")
def health_check():
    logger.info("Health check status: OK")
