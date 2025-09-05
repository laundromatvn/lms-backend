from fastapi import APIRouter
from pydantic import BaseModel

from app.libs.mqtt import mqtt_service


router = APIRouter()


@router.get("/health-check")
async def root():
    return {"status": "ok"}
