from sqlalchemy.orm import Session

from app.models.permission import Permission
from app.models.user import User
from app.schemas.permission import PermissionEditRequest

    

class CreatePermissionOperation:
    def execute(self, db: Session, current_user: User, request: PermissionEditRequest) -> Permission:
        if not self._has_permission(current_user):
            raise PermissionError("You are not allowed to create permission")

        permission = Permission(
            code=request.code,
            name=request.name,
            description=request.description,
            is_enabled=request.is_enabled,
        )
        db.add(permission)
        db.commit()
        db.refresh(permission)
        
        return permission
    
    def _has_permission(self, current_user: User) -> bool:
        return current_user.is_admin


