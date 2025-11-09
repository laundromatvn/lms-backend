from uuid import UUID
from sqlalchemy.orm import Session

from app.models.tenant import Tenant
from app.models.tenant_member import TenantMember
from app.models.user import User
from app.models.store import Store
from app.libs.database import with_db_session_classmethod
from app.schemas.store import (
    AddStoreRequest,
    ListStoreQueryParams,
    UpdateStoreRequest,
)

class StoreOperation:

    @classmethod
    @with_db_session_classmethod
    def get(
        cls,
        db: Session,
        current_user: User,
        store_id: UUID
    ) -> Store:
        authorized_tenants = (
            db.query(TenantMember)
            .filter(TenantMember.user_id == current_user.id)
            .filter(TenantMember.is_enabled == True)
            .all()
        )
        
        authorized_tenant_ids = [tenant.tenant_id for tenant in authorized_tenants]

        store = (
            db.query(Store)
            .filter(Store.id == store_id)
            .filter(Store.tenant_id.in_(authorized_tenant_ids))
            .first()
        )
        if not store:
            raise ValueError("Store not found")

        return store

    @classmethod
    @with_db_session_classmethod
    def list(
        cls,
        db: Session,
        current_user: User,
        query_params: ListStoreQueryParams
    ) -> tuple[int, list[Store]]:
        authorized_tenants = (
            db.query(TenantMember.tenant_id)
            .filter(TenantMember.user_id == current_user.id)
            .filter(TenantMember.is_enabled == True)
            .all()
        )

        authorized_tenant_ids = [tenant.tenant_id for tenant in authorized_tenants]

        base_query = (
            db.query(
                *Store.__table__.columns,
                Tenant.name.label("tenant_name"),
            )
            .join(Tenant, Store.tenant_id == Tenant.id)
            .filter(Store.tenant_id.in_(authorized_tenant_ids))
        )

        if query_params.tenant_id:
            base_query = base_query.filter(Store.tenant_id == query_params.tenant_id)

        if query_params.status:
            base_query = base_query.filter(Store.status == query_params.status)

        total = base_query.count()
        stores = (
            base_query
            .offset((query_params.page - 1) * query_params.page_size)
            .limit(query_params.page_size)
            .all()
        )
        
        return total, stores

    @classmethod
    @with_db_session_classmethod
    def create(
        cls,
        db: Session,
        current_user: User,
        request: AddStoreRequest,
    ) -> Store:
        if not cls._has_permission(current_user, request.tenant_id):
            raise PermissionError("You don't have permission to create store")

        store = Store(
            created_by=current_user.id,
            updated_by=current_user.id,
            name=request.name,
            address=request.address,
            longitude=request.longitude,
            latitude=request.latitude,
            contact_phone_number=request.contact_phone_number,
            tenant_id=request.tenant_id,
        )
        db.add(store)
        db.commit()
        db.refresh(store)

        return store
    
    @classmethod
    @with_db_session_classmethod
    def update_partially(
        cls,
        db: Session,
        current_user: User,
        store_id: UUID,
        request: UpdateStoreRequest,
    ) -> Store:
        store = db.query(Store).filter_by(id=store_id).first()
        if not store:
            raise ValueError("Store not found")

        if not cls._has_permission(current_user, store.tenant_id):
            raise PermissionError("You don't have permission to update store")
        
        update_data = request.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(store, field):
                setattr(store, field, value)
        
        store.updated_by = current_user.id
        
        db.commit()
        db.refresh(store)
        
        return store

    @classmethod
    @with_db_session_classmethod
    def _has_permission(cls, db: Session, created_by: User, tenant_id: UUID) -> bool:
        """
        Only admin or tenant admin can create store
        """
        if created_by.is_admin:
            return True

        authorized_tenant_members = (
            db.query(TenantMember)
            .filter(TenantMember.user_id == created_by.id)
            .filter(TenantMember.tenant_id == tenant_id)
            .filter(TenantMember.is_enabled == True)
            .all()
        )
        
        return len(authorized_tenant_members) > 0
