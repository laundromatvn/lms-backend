from typing import Dict

from app.models.user import UserRole
from app.policies.base import BasePolicies


class PortalStorePolicies(BasePolicies):
    
    required_permissions = [
        "store.list",
        "store.get",
        "store.create",
        "store.update",
        "store.delete",
        "store.get_payment_methods",
        "store.update_payment_methods",
    ]
    
    def has_portal_store_basic_view_access(self) -> bool:
        return "store.list" in self.enabled_policies
    
    def has_portal_store_management_access(self) -> bool:
        has_create_access = "store.create" in self.enabled_policies
        has_update_access = "store.update" in self.enabled_policies
        has_delete_access = "store.delete" in self.enabled_policies
        
        is_allowed_roles = self.current_user.role in [UserRole.ADMIN, UserRole.TENANT_ADMIN]
        
        return has_create_access and has_update_access and has_delete_access and is_allowed_roles
    
    def has_portal_store_payment_methods_view_access(self) -> bool:
        is_allowed_roles = self.current_user.role in [UserRole.ADMIN, UserRole.TENANT_ADMIN]

        return "store.get_payment_methods" in self.enabled_policies and is_allowed_roles
    
    def has_portal_store_payment_methods_management_access(self) -> bool:
        is_allowed_roles = self.current_user.role in [UserRole.ADMIN, UserRole.TENANT_ADMIN]
        
        return "store.update_payment_methods" in self.enabled_policies and is_allowed_roles
    
    def access(self) -> Dict[str, bool]:
        return {
            "portal_store_basic_view": self.has_portal_store_basic_view_access(),
            "portal_store_management": self.has_portal_store_management_access(),
            "portal_store_payment_methods_view": self.has_portal_store_payment_methods_view_access(),
            "portal_store_payment_methods_management": self.has_portal_store_payment_methods_management_access(),
        }

