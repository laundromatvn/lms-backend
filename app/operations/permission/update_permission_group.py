from uuid import UUID

from sqlalchemy.orm import Session, Query

from app.models.permission_group import PermissionGroup
from app.models.tenant_member import TenantMember
from app.models.user import User
from app.schemas.permission import PermissionGroupUpdatePayload


class UpdatePermissionGroupOperation:

    def __init__(
        self,
        db: Session,
        current_user: User,
        permission_group_id: UUID,
        payload: PermissionGroupUpdatePayload,
    ):
        self.db = db
        self.current_user = current_user
        self.permission_group_id = permission_group_id
        self.payload = payload
        self.tenant_members = None
        self.permission_group = None

    def execute(self) -> None:
        self._validate()
        self._update()

    def _validate(self) -> None:
        self._get_permission_group()
        self._validate_tenant_members()
        self._validate_payload()

    def _get_permission_group(self):
        self.permission_group = (
            self.db.query(PermissionGroup)
            .filter(PermissionGroup.id == self.permission_group_id)
            .first()
        )
        if not self.permission_group:
            raise ValueError(f"Permission group with ID {self.permission_group_id} not found")

    def _validate_tenant_members(self):
        if self.current_user.is_admin:
            return

        self.tenant_members = (
            self.db.query(TenantMember)
            .filter(TenantMember.user_id == self.current_user.id)
            .filter(TenantMember.is_enabled == True)
            .first()
        )
        if not self.tenant_members:
            raise PermissionError("You are not a member of this tenant")

        if self.current_user.is_tenant_admin:
            return

        if self.permission_group.tenant_id and self.permission_group.tenant_id != self.tenant_members.tenant_id:
            raise PermissionError("You are not allowed to update the tenant of this permission group")

    def _validate_payload(self):
        if self.payload.tenant_id and not self.current_user.is_admin:
            raise PermissionError("You are not allowed to update the tenant of this permission group")

    def _update(self):
        payload_dict = self.payload.model_dump(exclude_unset=True)
        if not payload_dict:
            return

        for field, value in payload_dict.items():
            if hasattr(self.permission_group, field):
                setattr(self.permission_group, field, value)

        self.permission_group.updated_by = self.current_user.id

        self.db.add(self.permission_group)
        self.db.commit()