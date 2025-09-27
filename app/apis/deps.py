from fastapi import HTTPException, Header
from typing import Optional

from app.core.logging import logger
from app.utils.security.jwt import verify_token


def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401)

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401)
        return verify_token(token)
    except Exception as e:
        logger.error("Invalid authorization header format", error=str(e))
        raise HTTPException(status_code=401)
