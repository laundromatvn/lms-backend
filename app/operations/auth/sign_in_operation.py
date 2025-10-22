from datetime import timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from app.core.config import settings
from app.libs.database import with_db_session_classmethod
from app.models.tenant_member import TenantMember
from app.models.user import User, UserRole
from app.utils.security import jwt
from app.schemas.auth import SignInRequest


class SignInOperation:

    @classmethod
    @with_db_session_classmethod
    async def execute(cls, db: Session, request: SignInRequest) -> tuple[User, str, str]:
        if request.email:
            user = db.query(User).filter(User.email == request.email).first()
        elif request.phone:
            user = db.query(User).filter(User.phone == request.phone).first()
        else:
            raise ValueError("Email or phone is required")

        if not user:
            raise NoResultFound("User not found")

        if not user.verify_password(request.password):
            raise NoResultFound("Invalid password")

        payload = cls.get_payload(user)
        temporary_access_token = jwt.create_access_token(
            payload,
            expires_delta=timedelta(seconds=settings.JWT_TEMPORARY_ACCESS_TOKEN_EXPIRE_SECONDS)
        )
        temp_access_token_payload = jwt.create_refresh_token(
            payload,
            expires_delta=timedelta(seconds=settings.JWT_REFRESH_TOKEN_EXPIRE_SECONDS)
        )

        return user, temporary_access_token, temp_access_token_payload
    
    @classmethod
    @with_db_session_classmethod
    def get_payload(cls, db: Session, user: User) -> dict:
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
        