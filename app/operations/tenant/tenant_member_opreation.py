from sqlalchemy.orm import Session

from app.libs.database import with_db_session_classmethod
from app.models.tenant_member import TenantMember
from app.models.user import User
from app.schemas.tenant_member import TenantMemberCreate



class TenantMemberOperation:

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
    def _have_permission(cls, db: Session, current_user: User, tenant_member: TenantMember) -> bool:
        # TODO: Implement permission check
        
        return True
