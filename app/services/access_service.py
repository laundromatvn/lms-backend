from sqlalchemy.orm import Session

from app.models.user import User
from app.policies.portal_overview_policies import PortalOverviewPolicies
from app.policies.portal_policies import PortalPolicies
from app.policies.permission_policies import PermissionPolicies


ACCESS_POLICIES = {
    "portal": PortalPolicies,
    "portal_dashboard_overview": PortalOverviewPolicies,
}


class AccessService:
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user

    def get_access(self, name: str) -> bool:
        if name not in ACCESS_POLICIES:
            raise ValueError(f"Unsupported access name: {name}")

        policies = ACCESS_POLICIES[name](self.db, self.current_user)

        return policies.access()

