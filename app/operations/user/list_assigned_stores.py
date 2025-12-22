from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.tenant_member import TenantMember
from app.models.store import Store
from app.models.store_member import StoreMember
from app.models.user import User
from app.schemas.user import ListAssignedStoresQueryParams


class ListAssignedStoresOperation:

    def __init__(self, current_user: User, user_id: UUID, query_params: ListAssignedStoresQueryParams):
        self.current_user = current_user
        self.user_id = user_id
        self.query_params = query_params

    def execute(self, db: Session) -> tuple[int, List[Store]]:
        self._validate(db)

        base_query = (
            db.query(Store)
            .join(StoreMember, Store.id == StoreMember.store_id)
            .filter(StoreMember.user_id == self.user_id)
        )
        
        total = base_query.count()
        stores = (
            base_query
            .offset((self.query_params.page - 1) * self.query_params.page_size)
            .limit(self.query_params.page_size)
            .all()
        )

        return total, stores

    def _validate(self, db: Session) -> None:
        if self.current_user.is_admin:
            return

        if not self._is_managed_member(db):
            raise PermissionError("You are not a managed member of this store")

    def _is_managed_member(self, db: Session) -> bool:
        """
        Each user can only be a member of one tenant at a time.
        """
        current_user_tenant_id = (
            db.query(TenantMember.tenant_id)
            .filter(TenantMember.user_id == self.current_user.id)
            .scalar()
        )

        user_tenant_id = (
            db.query(TenantMember.tenant_id)
            .filter(TenantMember.user_id == self.user_id)
            .scalar()
        )

        return current_user_tenant_id == user_tenant_id
