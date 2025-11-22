from fastapi import APIRouter

from app.apis.v1.dashboard.overview import router as overview_router
from app.apis.v1.dashboard.access import router as access_router


router = APIRouter()

router.include_router(overview_router, prefix="/overview", tags=["Dashboard Overview"])
router.include_router(access_router, prefix="/access", tags=["Dashboard Access"])

