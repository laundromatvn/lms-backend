from fastapi import APIRouter
from pydantic import BaseModel

from app.apis import v1


router = APIRouter(prefix="/api")


@router.get("/health-check")
async def root():
    return {"status": "ok"}


router.include_router(v1.router, prefix="/v1")
