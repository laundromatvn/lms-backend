from fastapi import APIRouter, HTTPException

from app.core.logging import logger
from app.operations.auth.auth_session_operation import AuthSessionOperation
from app.schemas.auth import (
    RefreshTokenResponse,
    GenerateTokenByOneTimeAccessTokenRequest,
)
from app.schemas.auth_session import AuthSession
from app.operations.auth.one_time_access_token_operation import OneTimeAccessTokenOperation


router = APIRouter()


@router.post("/sso/generate-sign-in-session", response_model=AuthSession)
async def generate_sign_in_session():
    try:
        return await AuthSessionOperation.create()
    except Exception as e:
        logger.error("Generate SSO sign in session failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sso/session/{session_id}", response_model=AuthSession)
async def get_sign_in_session(session_id: str):
    try:
        return await AuthSessionOperation.get(session_id)
    except Exception as e:
        logger.error("Get SSO sign in session failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sso/session/{session_id}/proceed", response_model=AuthSession)
async def proceed_sign_in_session(session_id: str):
    try:
        return await AuthSessionOperation.mark_as_in_progress(session_id)
    except Exception as e:
        logger.error("Proceed SSO sign in session failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sso/sign-in-by-one-time-access-token", response_model=RefreshTokenResponse)
async def sign_in_by_one_time_access_token(request: GenerateTokenByOneTimeAccessTokenRequest):
    """
    Sign in by one time access token.
    """
    try:
        access_token, refresh_token = await OneTimeAccessTokenOperation.generate_tokens(request.one_time_access_token)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
    except ValueError as e:
        logger.error("Sign in by one time access token failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Sign in by one time access token failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
