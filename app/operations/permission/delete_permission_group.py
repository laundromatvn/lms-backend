from uuid import UUID

from sqlalchemy.orm import Session, Query

from app.models.permission_group import PermissionGroup
from app.models.tenant import Tenant
from app.models.user import User


class DeletePermissionGroupOperation:

    def __init__(self, db: Session, current_user: User, permission_group_id: UUID):
        self.db = db
        self.current_user = current_user
        self.permission_group_id = permission_group_id

    def execute(self) -> None:
        base_query = (
            self.db.query(PermissionGroup)
            .filter(PermissionGroup.id == self.permission_group_id)
        )
        if not base_query:
            raise ValueError(f"Permission group with ID {self.permission_group_id} not found")
        
        base_query = self._apply_scope(base_query)

        permission_group = base_query.first()
        if not permission_group:
            raise ValueError(f"Permission group with ID {self.permission_group_id} not found")

        self.db.delete(permission_group)
        self.db.commit()

    def _apply_scope(self, base_query: Query) -> Query:
        if self.current_user.is_admin:
            return base_query

        if self.current_user.is_tenant_admin:
            return base_query.filter(
                PermissionGroup.tenant_id == self.current_user.tenant_id,
                PermissionGroup.tenant_id == None,
            )

        raise PermissionError("You are not allowed to delete this permission group")
