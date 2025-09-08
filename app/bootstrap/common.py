from contextlib import asynccontextmanager
from typing import AsyncGenerator
import os
import time

from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import configure_logging, logger
from app.libs import mqtt
from app.libs import redis


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    bootstrap_services()
    try:
        yield
    finally:
        shutdown_services()
        
        
def bootstrap_services():
    logger.info("starting", app=settings.app_name)
    init_timezone_and_logging()
    mqtt.start()
    redis.start()


def shutdown_services():
    logger.info("stopped", app=settings.app_name)
    mqtt.stop()
    redis.stop()


def init_timezone_and_logging():
    os.environ["TZ"] = settings.timezone_name
    try:
        time.tzset()
    except AttributeError:
        pass
    configure_logging(settings.log_level)
