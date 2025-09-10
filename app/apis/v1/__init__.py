from fastapi import APIRouter

from app.apis.v1 import actions
from app.apis.v1 import tasks
from app.apis.v1 import auth


router = APIRouter()

router.include_router(actions.router, prefix="/actions")
router.include_router(auth.router)
router.include_router(tasks.router, prefix="/tasks")
