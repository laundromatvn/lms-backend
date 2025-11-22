from sqlalchemy.orm import Session

from app.policies.base import BasePolicies
from app.models.user import User


class PortalPolicies(BasePolicies):
    def __init__(self, db: Session, current_user: User):
        super().__init__(db, current_user, ["portal_laundry_foundation_management", "portal_system_management"])

    def preload_policies(self) -> None:
        self.portal_laundry_foundation_management_enabled = "portal_laundry_foundation_management" in self.enabled_policies
        self.portal_system_management_enabled = "portal_system_management" in self.enabled_policies

    def can_access_portal_laundry_foundation_management(self) -> bool:
        return self.portal_laundry_foundation_management_enabled and self.current_user.is_admin
    
    def can_access_portal_system_management(self) -> bool:
        return self.portal_system_management_enabled and self.current_user.is_admin

