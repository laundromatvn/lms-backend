from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.tenant_member import TenantMember
from app.models.store import Store
from app.models.store_member import StoreMember
from app.models.user import User
from app.schemas.store_members import ListStoreMembersQueryParams, StoreMemberListSerializer


class ListStoreMembersOperation:

    def __init__(self, current_user: User, store_id: UUID, query_params: ListStoreMembersQueryParams):
        self.current_user = current_user
        self.store_id = store_id
        self.query_params = query_params

    def execute(self, db: Session) -> tuple[int, List[StoreMemberListSerializer]]:
        base_query = (
            db.query(
                StoreMember.id.label("id"),
                StoreMember.created_at.label("created_at"),
                User.id.label("user_id"),
                User.email.label("email"),
                User.phone.label("phone"),
                User.role.label("role"),
                User.status.label("status"),
            )
            .join(StoreMember, User.id == StoreMember.user_id)
            .filter(StoreMember.store_id == self.store_id)
        )

        total = base_query.count()
        store_members = (
            base_query
            .offset((self.query_params.page - 1) * self.query_params.page_size)
            .limit(self.query_params.page_size)
            .all()
        )

        return total, store_members
    
    def _validate(self, db: Session) -> None:
        if self.current_user.is_admin:
            return
        
        if not self._is_store_owner(db):
            raise PermissionError("You are not the owner of this store")

    def _is_store_owner(self, db: Session) -> bool:
        return (
            db.query(Store)
            .join(TenantMember, Store.tenant_id == TenantMember.tenant_id)
            .filter(
                TenantMember.user_id == self.current_user.id,
                Store.id == self.store_id,
            )
            .first() is not None
        )
