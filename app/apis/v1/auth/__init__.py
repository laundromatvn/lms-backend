from fastapi import APIRouter

from app.apis.v1.auth.auth import router as auth_router
from app.apis.v1.auth.profile import router as profile_router
from app.apis.v1.auth.sso import router as sso_router


router = APIRouter()

router.include_router(auth_router, tags=["Authentication"])
router.include_router(profile_router, tags=["Profile"])
router.include_router(sso_router, tags=["SSO"])


