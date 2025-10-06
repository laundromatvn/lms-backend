from fastapi import APIRouter, Depends, HTTPException

from app.models.user import User
from app.schemas.user import (
    UserSerializer,
    UpdateUserRequest,
    ResetPasswordRequest,
    CreateUserRequest,
)
from app.apis.deps import get_current_user
from app.operations.user.user_operation import UserOperation


router = APIRouter()


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return current_user.to_dict()


@router.post("/{user_id}/reset-password", response_model=UserSerializer)
def reset_password(
    user_id: str,
    request: ResetPasswordRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        user = UserOperation.reset_password(current_user, user_id, request)
        return user
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=UserSerializer)
def create_user(
    request: CreateUserRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        user = UserOperation.create(current_user, request)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}", response_model=UserSerializer)
def get_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
):
    try:
        user = UserOperation.get(current_user, user_id)
        return user
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{user_id}", response_model=UserSerializer)
def update_user(
    user_id: str,
    request: UpdateUserRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        user = UserOperation.update_partially(current_user, user_id, request)
        return user
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
