from app.utils.security import jwt
from app.schemas.auth import RefreshTokenRequest


class RefreshTokenOperation:

    @classmethod
    def execute(cls, request: RefreshTokenRequest) -> tuple[str, str]:
        user = jwt.verify_token(request.refresh_token)

        payload = {
            "user_id": str(user.id),
        }
        access_token = jwt.create_access_token(payload)
        refresh_token = jwt.create_refresh_token(payload)
        
        return access_token, refresh_token
