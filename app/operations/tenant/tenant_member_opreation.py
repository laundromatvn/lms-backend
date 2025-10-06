from sqlalchemy.orm import Session

from app.libs.database import with_db_session_classmethod
from app.models.tenant import Tenant
from app.models.tenant_member import TenantMember
from app.models.user import User
from app.schemas.tenant_member import TenantMemberCreate, ListTenantMemberQueryParams


class TenantMemberOperation:
    
    @classmethod
    @with_db_session_classmethod
    def list(
        cls,
        db: Session,
        current_user: User,
        query_params: ListTenantMemberQueryParams
    ) -> tuple[int, list[TenantMember]]:
        base_query = (
            db.query(
                *TenantMember.__table__.columns,
                User.email.label("user_email"),
                User.phone.label("user_phone"),
                User.role.label("user_role"),
                User.status.label("user_status"),
                Tenant.name.label("tenant_name"),
            )
            .join(User, TenantMember.user_id == User.id)
            .join(Tenant, TenantMember.tenant_id == Tenant.id)
        )

        if query_params.tenant_id:
            base_query = base_query.filter(TenantMember.tenant_id == query_params.tenant_id)
        
        total = base_query.count()
        tenant_members = (
            base_query
            .order_by(
                TenantMember.tenant_id.desc(),
            )
            .offset((query_params.page - 1) * query_params.page_size)
            .limit(query_params.page_size)
            .all()
        )
        
        return total, tenant_members

    @classmethod
    @with_db_session_classmethod
    def add(cls, db: Session, current_user: User, tenant_member: TenantMemberCreate) -> TenantMember:
        if not cls._have_permission(current_user, tenant_member):
            raise PermissionError("You are not allowed to add tenant member")
        
        is_exists = db.query(TenantMember).filter(
            TenantMember.tenant_id == tenant_member.tenant_id,
            TenantMember.user_id == tenant_member.user_id,
        ).first()
        if is_exists:
            raise ValueError("Tenant member already exists")

        tenant_member = TenantMember(
            tenant_id=tenant_member.tenant_id,
            user_id=tenant_member.user_id,
            is_enabled=True,
        )
        
        db.add(tenant_member)
        db.commit()
        db.refresh(tenant_member)
        
        return tenant_member

    @classmethod
    @with_db_session_classmethod
    def get(cls, db: Session, current_user: User, tenant_member_id: str) -> TenantMember:
        tenant_member = (
            db.query(
                *TenantMember.__table__.columns,
                User.email.label("user_email"),
                User.phone.label("user_phone"),
                User.role.label("user_role"),
                User.status.label("user_status"),
                Tenant.name.label("tenant_name"),
            )
            .join(User, TenantMember.user_id == User.id)
            .join(Tenant, TenantMember.tenant_id == Tenant.id)
            .filter(TenantMember.id == tenant_member_id)
            .first()
        )
        if not tenant_member:
            raise ValueError("Tenant member not found")

        if not cls._have_permission(current_user, tenant_member):
            raise PermissionError("You are not allowed to get this tenant member")

        return tenant_member

    @classmethod
    @with_db_session_classmethod
    def _have_permission(cls, db: Session, current_user: User, tenant_member: TenantMember) -> bool:
        # TODO: Implement permission check
        
        return True
