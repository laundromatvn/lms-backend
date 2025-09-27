from fastapi import APIRouter, Depends

from app.models.user import User
from app.schemas.user import UserSerializer
from app.apis.deps import get_current_user


router = APIRouter()


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return current_user.to_dict()
