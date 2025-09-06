from fastapi import APIRouter

from app.apis.v1.actions import demo


router = APIRouter()

router.include_router(demo.router, prefix="/demo")
