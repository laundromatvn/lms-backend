from collections.abc import Callable
import time
import os

from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import logger


def bootstrap_services(
    app: FastAPI = None,
    custom_callback: Callable = None,
):
    logger.info("starting", app=settings.APP_NAME)
    init_timezone_and_logging()

    if custom_callback:
        custom_callback(app)


def shutdown_services(
    app: FastAPI = None,
    custom_callback: Callable = None,
):
    logger.info("stopped", app=settings.APP_NAME)

    if custom_callback:
        custom_callback(app)


def init_timezone_and_logging():
    os.environ["TZ"] = settings.TIMEZONE_NAME
    try:
        time.tzset()
    except AttributeError:
        pass
