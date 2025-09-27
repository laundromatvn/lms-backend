from fastapi import APIRouter

from app.apis.v1.auth import router as auth_router
from app.apis.v1.user import router as user_router


router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(user_router, prefix="/user", tags=["User"])
