from uuid import UUID
from sqlalchemy.orm import Session, Query

from app.models.user import User
from app.models.store import Store
from app.models.store_member import StoreMember
from app.models.tenant import Tenant
from app.models.tenant_member import TenantMember


class DeleteStoreOperation:

    def __init__(
        self, 
        db: Session, 
        current_user: User, 
        store_id: UUID,
    ):
        self.db = db
        self.current_user = current_user
        self.store_id = store_id

    def execute(self) -> None:
        self.store = self.db.query(Store).filter(Store.id == self.store_id).first()
        if not self.store:
            raise ValueError("Store not found")
        
        if not self._is_store_owner():
            raise PermissionError("You are not the owner of this store")

        self.store.soft_delete(self.current_user.id)
        self.db.add(self.store)
        self.db.commit()

    def _is_store_owner(self) -> bool:
        if self.current_user.is_admin:
            return True

        is_tenant_member = (
            self.db.query(Store)
            .join(TenantMember, Store.tenant_id == TenantMember.tenant_id)
            .filter(
                TenantMember.user_id == self.current_user.id,
                Store.id == self.store_id,
            )
            .first()
        )
        
        return is_tenant_member and self.current_user.is_tenant_admin
