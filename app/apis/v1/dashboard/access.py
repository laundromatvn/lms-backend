from fastapi import APIRouter, Depends  

from app.apis.deps import get_current_user
from app.enums.access.portal_access import PortalAccessEnum
from app.libs.database import get_db
from app.models.user import User
from app.policies.portal_overview_policies import PortalOverviewPolicies
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("")
async def get_overview_access(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    policies = PortalOverviewPolicies(db, current_user)

    return {
        PortalAccessEnum.PORTAL_DASHBOARD_OVERVIEW: policies.can_access_portal_dashboard_overview(),
        PortalAccessEnum.PORTAL_DASHBOARD_ORDER_MANAGEMENT: policies.can_access_portal_dashboard_order_management(),
        PortalAccessEnum.PORTAL_DASHBOARD_MACHINE_MANAGEMENT: policies.can_access_portal_dashboard_machine_management(),
        PortalAccessEnum.PORTAL_DASHBOARD_MACHINE_SETTING: policies.can_access_portal_dashboard_machine_setting(),
    }

