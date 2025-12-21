from uuid import UUID

from sqlalchemy.orm import Session

from app.models.tenant_member import TenantMember
from app.models.user import User, UserRole
from app.models.user import User


class DeleteTenantMemberOperation:

    def __init__(self, db: Session, current_user: User, tenant_member_id: UUID):
        self.db = db
        self.current_user = current_user
        self.tenant_member_id = tenant_member_id

    def execute(self) -> None:
        self.tenant_member = (
            self.db.query(TenantMember)
            .filter(TenantMember.id == self.tenant_member_id)
            .first()
        )
        if not self.tenant_member:
            raise ValueError("Tenant member not found")

        self._validate()

        self.db.delete(self.tenant_member)
        self.db.commit()

    def _validate(self) -> None:
        if self.current_user.is_admin:
            return

        if not self._is_managed_member():
            raise PermissionError("You are not allowed to delete this tenant member")

    def _is_managed_member(self) -> bool:
        return (
            self.db.query(TenantMember)
            .join(User, TenantMember.user_id == User.id)
            .filter(
                User.role == UserRole.TENANT_ADMIN,
                TenantMember.user_id == self.current_user.id,
                TenantMember.tenant_id == self.tenant_member.tenant_id,
            )
            .first() is not None
        )
