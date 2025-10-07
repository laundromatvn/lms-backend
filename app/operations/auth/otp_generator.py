from uuid import UUID

from app.libs.cache import cache_manager
from app.utils.security.generator import generate_otp


class OtpGenerator:
    
    CACHED_KEY_PREFIX: str = "otp:{otp}"
    CACHED_KEY_TEMPLATE: str = "otp:{otp}:{user_id}"
    
    @classmethod
    async def execute(
        cls, 
        user_id: UUID,
        max_attempts: int = 100,
        ttl_seconds: int = 600,
    ) -> str:
        """
        Generate a unique OTP for a user.
        """
        attempts = 0

        while attempts < max_attempts:
            attempts += 1
            otp = generate_otp()
            is_exists = cache_manager.get_keys(f"{cls.CACHED_KEY_PREFIX.format(otp=otp)}*")

            if is_exists:
                continue
            else:
                cache_manager.set(cls.CACHED_KEY_TEMPLATE.format(otp=otp, user_id=user_id), 1, ttl_seconds)
                return otp

        raise RuntimeError("Unable to generate unique OTP after maximum attempts")
