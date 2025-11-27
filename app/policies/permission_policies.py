from app.policies.base import BasePolicies


class PermissionPolicies(BasePolicies):
    required_permissions = [
        "portal_system_management",
    ]

    def preload_policies(self) -> None:
        self.portal_system_management_enabled = "portal_system_management" in self.enabled_policies

    def can_get_permission(self) -> bool:
        return self.portal_system_management_enabled and self.current_user.is_admin
    
    def can_list_permissions(self) -> bool:
        return self.portal_system_management_enabled and self.current_user.is_admin
    
    def can_create_permission(self) -> bool:
        return self.portal_system_management_enabled and self.current_user.is_admin
    
    def can_update_permission(self) -> bool:
        return self.portal_system_management_enabled and self.current_user.is_admin
    
    def can_delete_permission(self) -> bool:
        return self.portal_system_management_enabled and self.current_user.is_admin

