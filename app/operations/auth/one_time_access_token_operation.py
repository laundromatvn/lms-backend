from datetime import timedelta

from sqlalchemy.orm import Session
from app.libs.cache import cache_manager
from app.libs.database import with_db_session_classmethod
from app.models.user import User, UserRole
from app.models.tenant_member import TenantMember
from app.utils.security import jwt


class OneTimeAccessTokenOperation:

    CACHED_KEY_TEMPLATE: str = "one_time_access_token:{one_time_access_token}"

    @classmethod
    async def generate(cls, user: User) -> str:
        payload = cls._get_payload(user)
        one_time_access_token = jwt.create_access_token(
            data=payload,
            expires_delta=timedelta(seconds=300)
        )

        cached_key = cls.CACHED_KEY_TEMPLATE.format(one_time_access_token=one_time_access_token)
        cache_manager.set(cached_key, True, timedelta(seconds=300))

        return one_time_access_token

    @classmethod
    async def generate_tokens(cls, one_time_access_token: str) -> tuple[str, str]:
        cached_key = cls.CACHED_KEY_TEMPLATE.format(one_time_access_token=one_time_access_token)
        cached_data = cache_manager.get(cached_key)
        if not cached_data:
            raise ValueError("One time access token not found")
        
        cache_manager.delete(cached_key)

        user = jwt.verify_token(one_time_access_token)
        if not user:
            raise ValueError("Invalid one time access token")

        payload = cls._get_sign_in_payload(user)
        access_token = jwt.create_access_token(payload)
        refresh_token = jwt.create_refresh_token(payload)

        return access_token, refresh_token
    
    @classmethod
    @with_db_session_classmethod
    def _get_payload(cls, db: Session, user: User) -> dict:
        payload = {}
        
        # add user id
        payload["user_id"] = str(user.id)
        payload["is_one_time_access_token"] = True

        if user.role in [UserRole.TENANT_ADMIN, UserRole.TENANT_STAFF]:
            tenant_member = (
                db.query(TenantMember)
                .filter(TenantMember.user_id == user.id)
                .filter(TenantMember.is_enabled == True)
                .first()
            )
            if tenant_member:
                payload["tenant_id"] = str(tenant_member.tenant_id)

        return payload


    @classmethod
    @with_db_session_classmethod
    def _get_sign_in_payload(cls, db: Session, user: User) -> dict:
        payload = {}
        
        # add user id
        payload["user_id"] = str(user.id)

        if user.role in [UserRole.TENANT_ADMIN, UserRole.TENANT_STAFF]:
            tenant_member = (
                db.query(TenantMember)
                .filter(TenantMember.user_id == user.id)
                .filter(TenantMember.is_enabled == True)
                .first()
            )
            if tenant_member:
                payload["tenant_id"] = str(tenant_member.tenant_id)

        return payload