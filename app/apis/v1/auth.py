from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.exc import IntegrityError

from app.core.logging import logger
from app.schemas.auth import (
    RegisterLMSUserRequest,
    SignInRequest,
    SignInResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    VerifyOTPRequest,
)
from app.operations.auth.register_lms_user_operation import RegisterLMSUserOperation
from app.operations.auth.sign_in_operation import SignInOperation
from app.operations.auth.refresh_token_operation import RefreshTokenOperation
from app.apis.deps import get_current_user
from app.models.user import User


router = APIRouter()


@router.post("/lms/register")
def register(request: RegisterLMSUserRequest):
    try:
        user = RegisterLMSUserOperation.execute(request)
        return user.to_dict()
    except IntegrityError as e:
        logger.error("User registration failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("User registration failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sign-in", response_model=SignInResponse)
def sign_in(request: SignInRequest):
    try:
        access_token, refresh_token = SignInOperation.execute(request)
        return SignInResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )
    except Exception as e:
        logger.error("Sign in failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh-token", response_model=RefreshTokenResponse)
def refresh_token(request: RefreshTokenRequest):
    try:
        access_token, refresh_token = RefreshTokenOperation.execute(request)
        return RefreshTokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )
    except Exception as e:
        logger.error("Refresh token failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-email-otp")
def generate_email_otp(current_user: User = Depends(get_current_user)):
    logger.info("Generating email OTP", email=current_user.email)
    
    return {
        "message": "OTP generated successfully",
    }    


@router.post("/verify-otp")
def verify_otp(request: VerifyOTPRequest, current_user: User = Depends(get_current_user)):
    logger.info("Verifying OTP", email=current_user.email, otp=request.otp)
    
    return {
        "message": "OTP verified successfully",
    }
