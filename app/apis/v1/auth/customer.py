from fastapi import APIRouter, HTTPException, Depends

from pydantic import BaseModel

from app.serializers.users.user_serializer import UserSerializer
from app.serializers.auth.tokens_serializer import TokensSerializer
from app.operations.auth.register_customer_operation import RegisterCustomerOperation
from app.operations.auth.sign_in_operation import SignInOperation
from app.models.users.user import UserRole, User
from app.apis.deps import get_current_user


router = APIRouter(prefix="/customer")


class RegisterCustomerPayload(BaseModel):
    phone: str
    password: str


class SignInCustomerPayload(BaseModel):
    phone: str
    password: str


@router.post("/register", response_model=UserSerializer)
async def register(payload: RegisterCustomerPayload):
    result = RegisterCustomerOperation().execute(payload=payload.__dict__)

    if result.is_success:
        return result.data.to_dict()
    else:
        raise HTTPException(status_code=422, detail=result.error_message)


@router.post("/sign-in", response_model=TokensSerializer)
async def sign_in(payload: SignInCustomerPayload):
    result = SignInOperation().execute(payload=payload.__dict__, role=UserRole.CUSTOMER)

    if result.is_success:
        return result.data["tokens"]
    else:
        raise HTTPException(status_code=422, detail=result.error_message)


@router.get("/me", response_model=UserSerializer)
async def get_me(user: User = Depends(get_current_user)):
    """
    Get current authenticated user's profile information.
    
    Returns:
        UserSerializer: Current user's profile data
    """
    return user.to_dict()
