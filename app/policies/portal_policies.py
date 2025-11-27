from typing import Dict

from app.models.user import UserRole
from app.policies.base import BasePolicies


class PortalPolicies(BasePolicies):
    def has_portal_laundry_foundation_management_access(self) -> bool:
        return self.current_user.role in [UserRole.ADMIN, UserRole.TENANT_ADMIN, UserRole.TENANT_STAFF]
    
    def has_portal_system_management_access(self) -> bool:
        return self.current_user.is_admin

    def access(self) -> Dict[str, bool]:
        return {
            "portal_laundry_foundation_management": self.has_portal_laundry_foundation_management_access(),
            "portal_system_management": self.has_portal_system_management_access(),
        }

