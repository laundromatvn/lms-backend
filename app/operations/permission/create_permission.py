from sqlalchemy.orm import Session

from app.models.permission import Permission
from app.schemas.permission import PermissionEditRequest

    
class CreatePermissionOperation:
    def execute(self, db: Session, request: PermissionEditRequest) -> Permission:
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

