from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.apis.router import router as api_router
from app.bootstrap.common import lifespan
from app.core.config import settings


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
