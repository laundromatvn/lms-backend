from fastapi import APIRouter, Depends

from app.apis.v1.auth import customer, lms
from app.serializers.users.user_serializer import UserSerializer
from app.models.users.user import User
from app.apis.deps import get_current_user


router = APIRouter(prefix="/auth")

router.include_router(customer.router)
router.include_router(lms.router)


@router.get("/me", response_model=UserSerializer)
async def get_me(user: User = Depends(get_current_user)):
    return user.to_dict()
