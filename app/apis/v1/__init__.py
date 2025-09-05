from fastapi import APIRouter

from app.apis.v1.actions import demo


router = APIRouter(prefix="/actions")


router.include_router(demo.router, prefix="/demo")
