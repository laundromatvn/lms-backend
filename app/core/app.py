from contextlib import asynccontextmanager
from typing import AsyncGenerator
import os
import time

from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import configure_logging, logger
from app.apis.router import router as api_router
from app.libs.mqtt import start_service as start_mqtt, stop_service as stop_mqtt


def init_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        lifespan=lifespan,
    )
    app.include_router(api_router)
    return app


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
    start_mqtt()


def shutdown_services():
    logger.info("stopped", app=settings.app_name)
    stop_mqtt()


def init_timezone_and_logging():
    os.environ["TZ"] = settings.timezone_name
    try:
        time.tzset()
    except AttributeError:
        pass
    configure_logging(settings.log_level)
