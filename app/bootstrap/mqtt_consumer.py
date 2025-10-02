from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.bootstrap.common import bootstrap_services, shutdown_services
from app.core.config import settings
from app.libs import mqtt
from app.subcribers.register_controller_subcriber import RegisterControllerSubcriber


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
        bootstrap_services(app=_app, custom_callback=startup_callback)
        yield
    finally:
        shutdown_services(app=_app)


def startup_callback(_app: FastAPI) -> None:
    """Initialize MQTT and start subscribers"""
    # Start MQTT client
    mqtt.start()
    
    # Initialize and start RegisterControllerSubcriber
    register_controller_subscriber = RegisterControllerSubcriber(mqtt.mqtt_client)
    register_controller_subscriber.listen()


def on_startup(_app: FastAPI) -> None:
    mqtt.start()


def on_shutdown(_app: FastAPI) -> None:
    mqtt.stop()
