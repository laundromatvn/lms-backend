from typing import Dict

from app.models.user import UserRole
from app.policies.base import BasePolicies


class PortalOverviewPolicies(BasePolicies):
    required_permissions = [
        "dashboard.overview.get",
        "order.list",
        "machine.list",
        "machine.update"
    ]

    def has_portal_dashboard_overview_access(self) -> bool:
        is_allowed_roles = self.current_user.role in [UserRole.ADMIN, UserRole.TENANT_ADMIN]
        return "dashboard.overview.get" in self.enabled_policies and is_allowed_roles

    def has_portal_dashboard_order_management_access(self) -> bool:
        return "order.list" in self.enabled_policies

    def has_portal_dashboard_machine_management_access(self) -> bool:
        has_machine_list_access = "machine.list" in self.enabled_policies
        return has_machine_list_access

    def has_portal_dashboard_machine_setting_access(self) -> bool:
        is_allowed_roles = self.current_user.role in [UserRole.ADMIN, UserRole.TENANT_ADMIN]
        
        has_machine_update_access = "machine.update" in self.enabled_policies
        return has_machine_update_access and is_allowed_roles

    def access(self) -> Dict[str, bool]:
        return {
            "portal_dashboard_overview": self.has_portal_dashboard_overview_access(),
            "portal_dashboard_order_management": self.has_portal_dashboard_order_management_access(),
            "portal_dashboard_machine_management": self.has_portal_dashboard_machine_management_access(),
            "portal_dashboard_machine_setting": self.has_portal_dashboard_machine_setting_access(),
        }

