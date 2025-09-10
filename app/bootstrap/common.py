from collections.abc import Callable
import os
import time

from fastapi import FastAPI

from app.core import database
from app.core.config import settings
from app.core.logging import configure_logging, logger
from app.libs import mqtt
from app.libs import redis

        
def bootstrap_services(
    app: FastAPI = None,
    custom_callback: Callable = None,
):
    logger.info("starting", app=settings.app_name)
    init_timezone_and_logging()
    mqtt.start()
    redis.start()
    database.init()
    
    if custom_callback:
        custom_callback(app)


def shutdown_services(
    app: FastAPI = None,
    custom_callback: Callable = None,
):
    logger.info("stopped", app=settings.app_name)

    if custom_callback:
        custom_callback(app)

    mqtt.stop()
    redis.stop()
    database.close()


def init_timezone_and_logging():
    os.environ["TZ"] = settings.timezone_name
    try:
        time.tzset()
    except AttributeError:
        pass
    configure_logging(settings.log_level)
