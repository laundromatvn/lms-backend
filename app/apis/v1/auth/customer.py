from fastapi import APIRouter, HTTPException

from pydantic import BaseModel

from app.serializers.users.user_serializer import UserSerializer
from app.operations.auth.register_customer_operation import RegisterCustomerOperation


router = APIRouter(prefix="/customer")


class RegisterCustomerPayload(BaseModel):
    phone: str
    password: str


@router.post(
    "/register",
    response_model=UserSerializer
)
async def register(payload: RegisterCustomerPayload):
    result = RegisterCustomerOperation().execute(payload=payload.__dict__)

    if result.is_success:
        return result.data.to_dict()
    else:
        raise HTTPException(status_code=422, detail=result.error_message)
