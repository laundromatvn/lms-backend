from sqlalchemy.orm import Session

from app.models.permission_group import PermissionGroup
from app.models.tenant_member import TenantMember
from app.models.user import User
from app.schemas.permission import PermissionGroupCreatePayload

class CreatePermissionGroupOperation:

    def __init__(self, db: Session, current_user: User, payload: PermissionGroupCreatePayload):
        self.db = db
        self.current_user = current_user
        self.payload = payload

    def execute(self) -> None:        
        self._validate_user()

        permission_group = PermissionGroup(
            created_by=self.current_user.id,
            updated_by=self.current_user.id,
            name=self.payload.name,
            description=self.payload.description,
            is_enabled=self.payload.is_enabled,
        )
        
        if self.current_user.is_tenant_admin:
            permission_group.tenant_id = self.tenant_members.tenant_id

        self.db.add(permission_group)
        self.db.commit()

    def _validate_user(self) -> None:
        if self.current_user.is_admin:
            return

        if not self.current_user.is_tenant_admin:
            raise PermissionError("You are not allowed to create a permission group")

        self.tenant_members = (
            self.db.query(TenantMember)
            .filter(TenantMember.user_id == self.current_user.id)
            .filter(TenantMember.tenant_id == self.payload.tenant_id)
            .filter(TenantMember.is_enabled == True)
            .first()
        )
        if not self.tenant_members:
            raise PermissionError("You are not a member of this tenant")

        if self.payload.tenant_id and self.payload.tenant_id != self.tenant_members.tenant_id:
            raise PermissionError("You are not allowed to create a permission group for this tenant")
