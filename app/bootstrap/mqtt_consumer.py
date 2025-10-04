from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.bootstrap.common import bootstrap_services, shutdown_services
from app.core.config import settings
from app.core.logging import logger
from app.libs import mqtt
from app.subcribers import ON_STARTUP_SUBSCRIBERS


TITLE = f"{settings.APP_NAME}_mqtt_consumer"


def init() -> FastAPI:
    app = FastAPI(
        title=TITLE,
        lifespan=lifespan,
    )

    return app


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    try:
        # Bootstrap services and start MQTT
        bootstrap_services(app=_app, custom_callback=on_startup)
        yield
    finally:
        shutdown_services(app=_app, custom_callback=on_shutdown)


def on_startup(_app: FastAPI) -> None:
    mqtt.start()
    
    init_subscribers()


def on_shutdown(_app: FastAPI) -> None:
    mqtt.stop()


def init_subscribers() -> None:
    for subscriber in ON_STARTUP_SUBSCRIBERS:
        logger.info(f"Initializing subscriber: {subscriber.__name__}")
        subscriber(mqtt.mqtt_client).listen()
