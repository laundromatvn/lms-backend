from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from app.apis.deps import get_current_user
from app.enums.access.portal_access import PortalAccessEnum
from app.libs.database import get_db
from app.models.user import User
from app.policies.permission_policies import PermissionPolicies
from app.policies.portal_policies import PortalPolicies

router = APIRouter()


@router.get("/access")
async def get_portal_access(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    policies = PortalPolicies(db, current_user)

    return {
        PortalAccessEnum.PORTAL_LAUNDRY_FOUNDATION_MANAGEMENT: policies.can_access_portal_laundry_foundation_management(),
        PortalAccessEnum.PORTAL_SYSTEM_MANAGEMENT: policies.can_access_portal_system_management(),
    }


