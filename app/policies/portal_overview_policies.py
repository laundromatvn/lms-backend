from typing import Dict

from app.models.user import UserRole
from app.policies.base import BasePolicies


class PortalOverviewPolicies(BasePolicies):
    required_permissions = [
        "portal_dashboard_overview",
        "portal_dashboard_order_management",
        "portal_dashboard_machine_management",
        "portal_dashboard_machine_setting",
    ]

    def preload_policies(self) -> None:
        self.portal_dashboard_overview_enabled = "portal_dashboard_overview" in self.enabled_policies
        self.portal_dashboard_order_management_enabled = "portal_dashboard_order_management" in self.enabled_policies
        self.portal_dashboard_machine_management_enabled = "portal_dashboard_machine_management" in self.enabled_policies
        self.portal_dashboard_machine_setting_enabled = "portal_dashboard_machine_setting" in self.enabled_policies

    def can_access_portal_dashboard_overview(self) -> bool:
        is_allowed_roles = self.current_user.role in [UserRole.ADMIN, UserRole.TENANT_ADMIN]
        return self.portal_dashboard_overview_enabled and is_allowed_roles

    def can_access_portal_dashboard_order_management(self) -> bool:
        return self.portal_dashboard_order_management_enabled

    def can_access_portal_dashboard_machine_management(self) -> bool:
        return self.portal_dashboard_machine_management_enabled

    def can_access_portal_dashboard_machine_setting(self) -> bool:
        is_allowed_roles = self.current_user.role in [UserRole.ADMIN, UserRole.TENANT_ADMIN]
        return self.portal_dashboard_machine_setting_enabled and is_allowed_roles

    def access(self) -> Dict[str, bool]:
        return {
            "portal_dashboard_overview": self.can_access_portal_dashboard_overview(),
            "portal_dashboard_order_management": self.can_access_portal_dashboard_order_management(),
            "portal_dashboard_machine_management": self.can_access_portal_dashboard_machine_management(),
            "portal_dashboard_machine_setting": self.can_access_portal_dashboard_machine_setting(),
        }

