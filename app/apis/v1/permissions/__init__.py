from fastapi import APIRouter

from .permissions import router as permissions_router
from .access import router as access_router

router = APIRouter()


router.include_router(permissions_router, prefix="/permissions", tags=["Permissions"])
router.include_router(access_router, prefix="/access", tags=["Access"])


