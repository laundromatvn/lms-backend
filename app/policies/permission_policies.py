from sqlalchemy.orm import Session

from app.policies.base import BasePolicies
from app.models.user import User


class PermissionPolicies(BasePolicies):
    def __init__(self, db: Session, current_user: User):
        super().__init__(db, current_user, ["portal_system_management"])
        
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

