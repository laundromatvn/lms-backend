from fastapi import HTTPException, Depends, Header
from typing import Optional

from app.operations.auth.token.get_user_from_token_operation import GetUserFromTokenOperation


def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header is required")

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    result = GetUserFromTokenOperation().execute(token=token)
    if result.is_success:       
        return result.data
    else:
        raise HTTPException(status_code=401, detail=result.error_message)
