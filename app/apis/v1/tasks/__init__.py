from fastapi import APIRouter

from app.apis.v1.tasks import tasks


router = APIRouter()

router.include_router(tasks.router)
