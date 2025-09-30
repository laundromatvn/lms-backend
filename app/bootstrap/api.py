from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.apis.router import router as api_router
from app.bootstrap.common import bootstrap_services, shutdown_services
from app.core.config import settings


TITLE = f"{settings.APP_NAME}_api"


def init() -> FastAPI:
    app = FastAPI(
        title=TITLE,
        lifespan=lifespan,
        redirect_slashes=True,  # Enable automatic trailing slash redirects
    )

    # Add CORS middleware first, before any other middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOW_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
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
    pass


def on_shutdown(_app: FastAPI) -> None:
    shutdown_services(app=_app)
