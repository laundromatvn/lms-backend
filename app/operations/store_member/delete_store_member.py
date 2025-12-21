from uuid import UUID

from sqlalchemy.orm import Session

from app.models.tenant_member import TenantMember
from app.models.store import Store
from app.models.store_member import StoreMember
from app.models.user import User


class DeleteStoreMemberOperation:

    def __init__(self, current_user: User, store_member_id: UUID):
        self.current_user = current_user
        self.store_member_id = store_member_id
        self.store_member = None
        
    def execute(self, db: Session) -> None:
        self._preload(db)
        self._validate(db)

        db.delete(self.store_member)
        db.commit()
        
    def _preload(self, db: Session) -> None:
        self.store_member = db.query(StoreMember).filter(StoreMember.id == self.store_member_id).first()
        if not self.store_member:
            raise ValueError("Store member not found")

    def _validate(self, db: Session) -> None:
        if self.current_user.is_admin:
            return
        
        if not self._is_store_owner(db):
            raise PermissionError("You are not the owner of this store")
        
        if not self._is_managed_member(db):
            raise PermissionError("You are not a managed member of this store")

    def _is_store_owner(self, db: Session) -> bool:
        return (
            db.query(Store)
            .join(TenantMember, Store.tenant_id == TenantMember.tenant_id)
            .filter(
                TenantMember.user_id == self.current_user.id,
                Store.id == self.store_member.store_id,
            )
            .first() is not None
        )
    
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
            .filter(TenantMember.user_id == self.store_member.user_id)
            .scalar()
        )
        
        return current_user_tenant_id == user_tenant_id
