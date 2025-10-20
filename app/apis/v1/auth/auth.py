from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.exc import IntegrityError

from app.apis.deps import get_current_user
from app.core.logging import logger
from app.models.user import User
from app.operations.auth.auth_session_operation import AuthSessionOperation
from app.schemas.auth import (
    RegisterLMSUserRequest,
    SignInRequest,
    SignInResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    SendOTPResponse,
    SendOTPRequest,
    VerifyOTPRequest,
)
from app.operations.auth.register_lms_user_operation import RegisterLMSUserOperation
from app.operations.auth.sign_in_operation import SignInOperation
from app.operations.auth.refresh_token_operation import RefreshTokenOperation
from app.operations.auth.verify_otp_operation import VerifyOTPOperation
from app.operations.system_task_operation import SystemTaskOperation
from app.tasks.auth.send_otp_task import send_otp_task


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
        await AuthSessionOperation.mark_as_in_progress(request.session_id)
        access_token, refresh_token = await SignInOperation.execute(request)
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
async def send_otp(
    request: SendOTPRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        send_otp_task.apply_async(kwargs={
            "email": current_user.email, 
            "otp_action": request.action.value,
            "data": request.data,
        })
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
async def verify_otp(
    request: VerifyOTPRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        await VerifyOTPOperation.execute(current_user, request.otp, request.action)
        await AuthSessionOperation.mark_as_success(current_user, request.session_id)
        
        if request.session_id:
            SystemTaskOperation.mark_as_success(request.session_id)
        return {
            "message": "OTP verified successfully",
        }
    except ValueError as e:
        logger.error("Verify OTP validation failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Verify OTP failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


