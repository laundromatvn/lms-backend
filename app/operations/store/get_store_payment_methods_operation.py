from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.tenant_member import TenantMember
from app.models.store import Store
from app.models.user import User
from app.libs.database import with_db_session_for_class_instance
from app.schemas.store import PaymentMethod


class GetStorePaymentMethodsOperation:
    
    def __init__(self, current_user: User, store_id: UUID):
        self.current_user = current_user
        self.store_id = store_id

        self._preload()
        self._validate()

    def execute(self) -> List[PaymentMethod]:
        payment_methods = []
        
        for method in self.store.payment_methods:
            if not method.get('is_enabled'):
                continue

            payment_methods.append(method)

        return payment_methods

    @with_db_session_for_class_instance
    def _preload(self, db: Session) -> None:
        self.store = self._get_store(db)
        
    @with_db_session_for_class_instance
    def _validate(self, db: Session) -> None:
        if not self._has_permission(db):
            raise PermissionError("You are not allowed to get this store payment methods")

    def _get_store(self, db: Session) -> Store:
        return db.query(Store).filter(Store.id == self.store_id).first()

    def _has_permission(self, db: Session) -> bool:
        if self.current_user.is_admin:
            return True

        tenant_member = (
            db.query(TenantMember)
            .filter(TenantMember.user_id == self.current_user.id)
            .filter(TenantMember.tenant_id == self.store.tenant_id)
            .filter(TenantMember.is_enabled == True)
            .first()
        )

        return tenant_member is not None


