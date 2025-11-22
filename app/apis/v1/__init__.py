from fastapi import APIRouter

from app.apis.v1.auth import router as auth_router
from app.apis.v1.controller import router as controller_router
from app.apis.v1.dashboard import router as dashboard_router
from app.apis.v1.firmware import router as firmware_router
from app.apis.v1.firmware_deployment import router as firmware_deployment_router
from app.apis.v1.machine import router as machine_router
from app.apis.v1.tenant import router as tenant_router
from app.apis.v1.tenant_member import router as tenant_member_router
from app.apis.v1.store import router as store_router
from app.apis.v1.system_task import router as system_task_router
from app.apis.v1.order import router as order_router
from app.apis.v1.payment import router as payment_router
from app.apis.v1.permissions import router as permissions_router
from app.apis.v1.promotion_campaign import router as promotion_campaign_router
from app.apis.v1.vietqr import router as vietqr_router
from app.apis.v1.vnpay import router as vnpay_router
from app.apis.v1.user import router as user_router


router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(controller_router, prefix="/controller", tags=["Controller"])
router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
router.include_router(firmware_router, prefix="/firmware", tags=["Firmware"])
router.include_router(firmware_deployment_router, prefix="/firmware-deployment", tags=["Firmware Deployment"])
router.include_router(machine_router, prefix="/machine", tags=["Machine"])
router.include_router(tenant_router, prefix="/tenant", tags=["Tenant"])
router.include_router(tenant_member_router, prefix="/tenant-member", tags=["Tenant Member"])
router.include_router(store_router, prefix="/store", tags=["Store"])
router.include_router(system_task_router, prefix="/system-task", tags=["System Task"])
router.include_router(order_router, prefix="/order", tags=["Order"])
router.include_router(payment_router, prefix="/payment", tags=["Payment"])
router.include_router(permissions_router, prefix="/permission", tags=["Permissions"])
router.include_router(promotion_campaign_router, prefix="/promotion-campaign", tags=["Promotion Campaign"])
router.include_router(vietqr_router, prefix="/vietqr", tags=["VietQR"])
router.include_router(vnpay_router, prefix="/vnpay", tags=["VNPAY"])
router.include_router(user_router, prefix="/user", tags=["User"])


