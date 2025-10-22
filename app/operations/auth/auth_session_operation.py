from datetime import datetime, timedelta
from uuid import uuid4

from app.enums.auth_session import AuthSessionStatusEnum
from app.libs.cache import cache_manager
from app.schemas.auth_session import AuthSession
from app.operations.auth.one_time_access_token_operation import OneTimeAccessTokenOperation
from app.models.user import User


class AuthSessionOperation:
    
    CACHED_KEY_TEMPLATE: str = "auth_session:{session_id}"

    @classmethod
    async def create(cls, ttl_seconds: int = 3600) -> AuthSession:
        session = AuthSession(
            id=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            status=AuthSessionStatusEnum.NEW.value,
            expires_in=ttl_seconds,
            expires_at=datetime.now() + timedelta(seconds=ttl_seconds),
            data=None,
        )
        
        cached_key = cls.CACHED_KEY_TEMPLATE.format(session_id=session.id)
        cached_data = cls._to_cached_data(session)
        cache_manager.set(cached_key, cached_data, session.expires_in)

        return session

    @classmethod
    async def get(cls, session_id: str) -> AuthSession:
        cached_key = cls.CACHED_KEY_TEMPLATE.format(session_id=session_id)
        cached_data = cache_manager.get(cached_key)
        if not cached_data:
            raise ValueError("Session not found")
        return cls._to_session(cached_data)

    @classmethod
    async def update(cls, session_id: str, status: AuthSessionStatusEnum, data: dict) -> AuthSession | None:
        cached_key = cls.CACHED_KEY_TEMPLATE.format(session_id=session_id)
        cached_data = cache_manager.get(cached_key)
        if not cached_data:
            return None

        cached_data["status"] = status.value
        cached_data["data"] = data
        cache_manager.set(cached_key, cached_data, cached_data["expires_in"])
        
        return cls._to_session(cached_data)

    @classmethod
    async def delete(cls, session_id: str) -> None:
        cached_key = cls.CACHED_KEY_TEMPLATE.format(session_id=session_id)
        cache_manager.delete(cached_key)

    @classmethod
    async def mark_as_in_progress(cls, session_id: str) -> None:
        cached_key = cls.CACHED_KEY_TEMPLATE.format(session_id=session_id)
        cached_data = cache_manager.get(cached_key)
        if not cached_data:
            return None

        cached_data["status"] = AuthSessionStatusEnum.IN_PROGRESS.value
        cache_manager.set(cached_key, cached_data, cached_data["expires_in"])
        
        return cls._to_session(cached_data)
    
    @classmethod
    async def mark_as_success(cls, user: User, session_id: str) -> None:
        cached_key = cls.CACHED_KEY_TEMPLATE.format(session_id=session_id)
        cached_data = cache_manager.get(cached_key)
        if not cached_data:
            return None

        temp_access_token = await OneTimeAccessTokenOperation.generate(user)

        cached_data["status"] = AuthSessionStatusEnum.SUCCESS.value
        cached_data["data"] = temp_access_token
        
        cache_manager.set(cached_key, cached_data, cached_data["expires_in"])
        
        return cls._to_session(cached_data)
    
    @classmethod
    def _to_cached_data(cls, session: AuthSession) -> dict:
        data = session.model_dump()
        data["status"] = data["status"].value
        return data
    
    @classmethod
    def _to_session(cls, cached_data: dict) -> AuthSession:
        data = AuthSession(**cached_data)
        return data
