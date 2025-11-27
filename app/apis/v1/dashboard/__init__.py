from fastapi import APIRouter

from app.apis.v1.dashboard.overview import router as overview_router


router = APIRouter()

router.include_router(overview_router, prefix="/overview", tags=["Dashboard Overview"])

