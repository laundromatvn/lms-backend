from app.core.config import settings
from app.libs.cache import cache_manager
from app.models.user import User


class VerifyOTPOperation:

    CACHED_KEY_TEMPLATE: str = "otp:{otp}:{user_id}"

    @classmethod
    async def execute(cls, current_user: User, otp: str) -> None:
        if settings.APP_ENV != "production":
            return True

        cached_key = cls.CACHED_KEY_TEMPLATE.format(otp=otp, user_id=current_user.id)
        if not cache_manager.get(cached_key):
            raise ValueError("Invalid OTP")
