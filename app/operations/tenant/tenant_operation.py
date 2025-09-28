from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.libs.database import with_db_session_classmethod
from app.models.tenant_member import TenantMember
from app.models.user import User, UserRole
from app.models.tenant import Tenant
from app.schemas.tenant import (
    AddTenantRequest,
    UpdateTenantRequest,
    ListTenantQueryParams,
)


class TenantOperation:

    @classmethod
    @with_db_session_classmethod
    def add(cls, db: Session, created_by: User, request: AddTenantRequest) -> Tenant:
        if not created_by.is_admin:
            raise ValueError("Only admin can add tenant")
        
        existing_tenant = db.query(Tenant).filter(
            or_(
                Tenant.contact_email == request.contact_email,
                Tenant.contact_phone_number == request.contact_phone_number,
            )
        ).first()
        
        if existing_tenant:
            raise ValueError("Tenant with this email or phone number already exists")

        tenant = Tenant(
            created_by=created_by.id,
            updated_by=created_by.id,
            name=request.name,
            contact_email=request.contact_email,
            contact_phone_number=request.contact_phone_number,
            contact_full_name=request.contact_full_name,
            contact_address=request.contact_address,
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        return tenant

    @classmethod
    @with_db_session_classmethod
    def update_partially(cls, db: Session, updated_by: User, tenant_id: str, request: UpdateTenantRequest) -> Tenant:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise ValueError("Tenant not found")
        
        if not cls._have_permission(updated_by, tenant):
            raise PermissionError("You don't have permission to update this tenant")
        
        update_data = request.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(tenant, field):
                setattr(tenant, field, value)
        
        tenant.updated_by = updated_by.id

        db.commit()
        db.refresh(tenant)
        
        return tenant

    @classmethod
    @with_db_session_classmethod
    def get(cls, db: Session, current_user: User, tenant_id: str) -> Tenant:
        tenant = db.query(Tenant).get(tenant_id)
        if not tenant:
            raise ValueError("Tenant not found")

        if not cls._have_permission(current_user, tenant):
            raise PermissionError("You don't have permission to get this tenant")

        return tenant

    @classmethod
    @with_db_session_classmethod
    def list(cls, db: Session, current_user: User, query_params: ListTenantQueryParams) -> tuple[int, list[Tenant]]:
        base_query = db.query(Tenant)
        
        if query_params.status:
            base_query = base_query.filter(Tenant.status == query_params.status)

        total = base_query.count()
        tenants = (
            base_query
            .offset((query_params.page - 1) * query_params.page_size)
            .limit(query_params.page_size)
            .all()
        )

        return total, tenants

    @classmethod
    @with_db_session_classmethod
    def get_user_tenant(cls, db: Session, user_id: UUID) -> Tenant:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        if user.role not in [UserRole.TENANT_ADMIN, UserRole.TENANT_STAFF]:
            raise PermissionError("User is not a tenant admin or staff")
        
        tenant_member = db.query(TenantMember).filter(TenantMember.user_id == user_id).first()
        if not tenant_member:
            raise ValueError("User does not belong to any tenant")
        
        tenant = db.query(Tenant).filter(Tenant.id == tenant_member.tenant_id).first()
        if not tenant:
            raise ValueError("Tenant not found")

        return tenant

    @classmethod
    def _have_permission(cls, current_user: User, tenant: Tenant) -> bool:
        if current_user.is_admin:
            return True

        if current_user.id == tenant.created_by:
            return True

        return False
