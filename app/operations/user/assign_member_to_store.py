from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.tenant_member import TenantMember
from app.models.store import Store
from app.models.store_member import StoreMember
from app.models.user import User


class AssignMemberToStoreOperation:

    def __init__(self, current_user: User, user_id: UUID, store_ids: List[UUID]):
        self.current_user = current_user
        self.user_id = user_id
        self.store_ids = store_ids

    def execute(self, db: Session) -> None:
        self._validate(db)
        
        existing_store_members = (
            db.query(StoreMember)
            .filter(StoreMember.user_id == self.user_id)
            .all()
        )

        store_ids = [store_member.store_id for store_member in existing_store_members]
        new_store_ids = [store_id for store_id in self.store_ids if store_id not in store_ids]

        store_members = []
        for store_id in new_store_ids:
            store_members.append(StoreMember(
                store_id=store_id,
                user_id=self.user_id,
            ))
        db.add_all(store_members)
        db.commit()

    def _validate(self, db: Session) -> None:
        if self.current_user.is_admin:
            return
        
        if not self._is_store_owners(db):
            raise PermissionError("You are not the owner of this store")
        
        if not self._is_managed_member(db):
            raise PermissionError("You are not a managed member of this store")

    def _is_store_owners(self, db: Session) -> bool:
        store_owners = (
            db.query(Store)
            .join(TenantMember, Store.tenant_id == TenantMember.tenant_id)
            .filter(
                TenantMember.user_id == self.current_user.id,
                Store.id.in_(self.store_ids),
            )
            .all()
        )
        
        return len(store_owners) == len(self.store_ids)
    
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
