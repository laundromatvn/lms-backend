from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.exc import IntegrityError

from app.apis.deps import get_current_user
from app.core.logging import logger
from app.models.user import User
from app.schemas.auth import (
    RegisterLMSUserRequest,
    SignInRequest,
    SignInResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    SendOTPResponse,
    VerifyOTPRequest,
    LMSProfileResponse,
)
from app.operations.auth.register_lms_user_operation import RegisterLMSUserOperation
from app.operations.auth.sign_in_operation import SignInOperation
from app.operations.auth.refresh_token_operation import RefreshTokenOperation
from app.operations.tenant.tenant_operation import TenantOperation
from app.operations.auth.send_otp_operation import SendOTPOperation
from app.operations.auth.verify_otp_operation import VerifyOTPOperation


router = APIRouter()


@router.post("/lms/register")
async def register(request: RegisterLMSUserRequest):
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
async def sign_in(request: SignInRequest):
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
async def refresh_token(request: RefreshTokenRequest):
    try:
        access_token, refresh_token = RefreshTokenOperation.execute(request)
        return RefreshTokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )
    except Exception as e:
        logger.error("Refresh token failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-otp", response_model=SendOTPResponse)
async def send_otp(current_user: User = Depends(get_current_user)):
    try:
        await SendOTPOperation.execute(current_user.email)
        return {
            "message": "OTP sent successfully",
            "email": current_user.email,
            "expires_in_minutes": 10,
        }

    except ValueError as e:
        logger.error("Send OTP validation failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Send OTP failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify-otp")
async def verify_otp(request: VerifyOTPRequest, current_user: User = Depends(get_current_user)):
    try:
        await VerifyOTPOperation.execute(current_user, request.otp)
        return {
            "message": "OTP verified successfully",
        }
    except ValueError as e:
        logger.error("Verify OTP validation failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Verify OTP failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/lms-profile", response_model=LMSProfileResponse)
def get_lms_profile(current_user: User = Depends(get_current_user)):
    try:
        tenant = TenantOperation.get_user_tenant(current_user.id)
        return {
            "user": current_user,
            "tenant": tenant,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error("Get LMS profile failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
