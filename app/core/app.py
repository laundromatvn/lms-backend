from contextlib import asynccontextmanager
from typing import AsyncGenerator
import os
import time

from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.apis.router import router as api_router
from app.integrations.redis import RedisClient
from app.integrations.mqtt import MqttClient


logger = get_logger()


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
    # init_redis()
    # init_mqtt()
    # start_mqtt()


def shutdown_services():
    logger.info("stopped", app=settings.app_name)
    # stop_mqtt()
    # close_redis()


def init_timezone_and_logging():
    os.environ["TZ"] = settings.timezone_name
    try:
        time.tzset()
    except AttributeError:
        pass
    configure_logging(settings.log_level)


def init_redis():
    RedisClient.init(settings.redis_url)


def close_redis():
    RedisClient.close()


def init_mqtt():
    MqttClient.init(
        host=settings.mqtt_host,
        port=settings.mqtt_port,
        topic_prefix=settings.topic_prefix,
    )


def start_mqtt():
    MqttClient.start()


def stop_mqtt():
    MqttClient.stop()
