from typing import Dict

from app.policies.base import BasePolicies


class PortalPolicies(BasePolicies):
    required_permissions = [
        "portal_laundry_foundation_management",
        "portal_system_management",
    ]

    def preload_policies(self) -> None:
        self.portal_laundry_foundation_management_enabled = "portal_laundry_foundation_management" in self.enabled_policies
        self.portal_system_management_enabled = "portal_system_management" in self.enabled_policies

    def can_access_portal_laundry_foundation_management(self) -> bool:
        return self.portal_laundry_foundation_management_enabled
    
    def can_access_portal_system_management(self) -> bool:
        return self.portal_system_management_enabled and self.current_user.is_admin
    
    def access(self) -> Dict[str, bool]:
        return {
            "portal_laundry_foundation_management": self.can_access_portal_laundry_foundation_management(),
            "portal_system_management": self.can_access_portal_system_management(),
        }

