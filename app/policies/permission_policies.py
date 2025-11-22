from sqlalchemy.orm import Session

from app.enums.access.portal_access import PortalPermissionAccessEnum
from app.models.permission import Permission
from app.models.user import User


class PermissionPolicies:
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user
        
        self.preload_permissions()
        
    def preload_permissions(self) -> list[Permission]:
        self.portal_permission_management_enabled = (
            self.db.query(Permission)
                .filter_by(
                    code="portal_permission_management",
                    is_enabled=True,
                )
                .first() is not None
        )

    def can_access_portal_permission_management(self) -> bool:
        return self.portal_permission_management_enabled and self.current_user.is_admin
    
    def can_get_permission(self) -> bool:
        return self.portal_permission_management_enabled and self.current_user.is_admin
    
    def can_list_permissions(self) -> bool:
        return self.portal_permission_management_enabled and self.current_user.is_admin
    
    def can_create_permission(self) -> bool:
        return self.portal_permission_management_enabled and self.current_user.is_admin
    
    def can_update_permission(self) -> bool:
        return self.portal_permission_management_enabled and self.current_user.is_admin
    
    def can_delete_permission(self) -> bool:
        return self.portal_permission_management_enabled and self.current_user.is_admin

