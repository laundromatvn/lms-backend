from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.policies.base import BasePolicies


class PortalOverviewPolicies(BasePolicies):
    def __init__(self, db: Session, current_user: User):
        policy_codes = [
            "portal_dashboard_overview",
            "portal_dashboard_order_management",
            "portal_dashboard_machine_management",
            "portal_dashboard_machine_setting",
        ]

        super().__init__(db, current_user, policy_codes)

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

