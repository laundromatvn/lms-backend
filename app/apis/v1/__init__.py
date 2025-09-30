from fastapi import APIRouter

from app.apis.v1.auth import router as auth_router
from app.apis.v1.controller import router as controller_router
from app.apis.v1.machine import router as machine_router
from app.apis.v1.tenant import router as tenant_router
from app.apis.v1.tenant_member import router as tenant_member_router
from app.apis.v1.store import router as store_router
from app.apis.v1.user import router as user_router
from app.apis.v1.order import router as order_router


router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(controller_router, prefix="/controller", tags=["Controller"])
router.include_router(machine_router, prefix="/machine", tags=["Machine"])
router.include_router(tenant_router, prefix="/tenant", tags=["Tenant"])
router.include_router(tenant_member_router, prefix="/tenant-member", tags=["Tenant Member"])
router.include_router(store_router, prefix="/store", tags=["Store"])
router.include_router(user_router, prefix="/user", tags=["User"])
router.include_router(order_router, prefix="/order", tags=["Order"])
