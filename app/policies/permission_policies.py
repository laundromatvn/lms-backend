from app.policies.base import BasePolicies


class PermissionPolicies(BasePolicies):
    required_permissions = [
        "permission.list",
        "permission.get",
        "permission.create",
        "permission.update",
        "permission.delete",
    ]

    def has_permission_get_access(self) -> bool:
        return "permission.get" in self.enabled_policies and self.current_user.is_admin
    
    def has_permission_list_access(self) -> bool:
        return "permission.list" in self.enabled_policies and self.current_user.is_admin
    
    def has_permission_create_access(self) -> bool:
        return "permission.create" in self.enabled_policies and self.current_user.is_admin
    
    def has_permission_update_access(self) -> bool:
        return "permission.update" in self.enabled_policies and self.current_user.is_admin
    
    def has_permission_delete_access(self) -> bool:
        return "permission.delete" in self.enabled_policies and self.current_user.is_admin

