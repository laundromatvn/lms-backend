from uuid import UUID
from sqlalchemy.orm import Session

from app.models.tenant import Tenant
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
        store_id: UUID
    ) -> Store:
        store = db.query(Store).filter_by(id=store_id).first()
        if not store:
            raise ValueError("Store not found")
        
        # TODO: check permission of admin/tenant/customer

        return store

    @classmethod
    @with_db_session_classmethod
    def list(
        cls,
        db: Session,
        created_by: User,
        query_params: ListStoreQueryParams
    ) -> tuple[int, list[Store]]:
        base_query = db.query(Store)
        
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
        created_by: User,
        request: AddStoreRequest,
    ) -> Store:
        if not cls._has_permission(created_by, request.tenant_id):
            raise PermissionError("You don't have permission to create store")

        store = Store(
            created_by=created_by.id,
            updated_by=created_by.id,
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
        created_by: User,
        store_id: UUID,
        request: UpdateStoreRequest,
    ) -> Store:
        store = db.query(Store).filter_by(id=store_id).first()
        if not store:
            raise ValueError("Store not found")

        if not cls._has_permission(created_by, store.tenant_id):
            raise PermissionError("You don't have permission to update store")
        
        update_data = request.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(store, field):
                setattr(store, field, value)
        
        store.updated_by = created_by.id
        
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

        if not created_by.is_tenant_admin:
            return False

        created_by_tenant = db.query(Tenant).filter_by(id=tenant_id).first()
        if not created_by_tenant:
            return False

        return created_by_tenant.created_by == created_by.id
