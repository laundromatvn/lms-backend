from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.apis.router import router as api_router
from app.bootstrap.common import bootstrap_services, shutdown_services
from app.core.config import settings
from app.core.logging import logger
import app.core.database as database


APP_NAME = "api"
TITLE = f"{settings.app_name}_{APP_NAME}"


def init() -> FastAPI:
    app = FastAPI(
        title=TITLE,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)

    return app


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    bootstrap_services(app=_app, custom_callback=on_startup)
    try:
        yield
    finally:
        shutdown_services(app=_app, custom_callback=on_shutdown)


def on_startup(_app: FastAPI) -> None:
    if settings.auto_migrate:
        logger.info("Running automatic database migrations")
        migration_success = database.migrate(auto_migrate=True)
        if not migration_success:
            logger.warning("Database migration failed, continuing with startup")
        else:
            logger.info("Database migrations completed successfully")


def on_shutdown(_app: FastAPI) -> None:
    shutdown_services(app=_app)
