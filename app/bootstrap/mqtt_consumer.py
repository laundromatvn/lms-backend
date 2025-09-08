from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.bootstrap.common import bootstrap_services, shutdown_services
from app.core.config import settings
from app.core.logging import logger
from app.libs.mqtt import mqtt_client
from app.subscriber import subscriber_list, SubscriberManager


APP_NAME = "mqtt_consumer"
TITLE = f"{settings.app_name}_{APP_NAME}"


def init() -> FastAPI:
    app = FastAPI(
        title=TITLE,
        lifespan=lifespan,
    )

    return app


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    bootstrap_services(app=_app, custom_callback=_start_subscribers)

    try:
        yield
    finally:
        shutdown_services(app=_app, custom_callback=_stop_subscribers)


def _start_subscribers(app: FastAPI):
    try:
        logger.info("starting subscribers")
        manager = SubscriberManager(client=mqtt_client, subscribers=subscriber_list)
        manager.start()
        app.state.subscriber_manager = manager
    except Exception as exc:
        logger.error("subscriber_manager_start_error", error=str(exc))


def _stop_subscribers(app: FastAPI):
    manager = getattr(app.state, "subscriber_manager", None)
    if manager is not None:
        try:
            manager.stop()
        except Exception as exc:
            logger.error("subscriber_manager_stop_error", error=str(exc))
