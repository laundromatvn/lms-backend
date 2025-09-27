from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.bootstrap.common import shutdown_services
from app.core.config import settings


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
        yield
    finally:
        shutdown_services(app=_app)
