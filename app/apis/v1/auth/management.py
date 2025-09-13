from fastapi import APIRouter, HTTPException

from pydantic import BaseModel

from app.serializers.users.user_serializer import UserSerializer
from app.serializers.auth.tokens_serializer import TokensSerializer
from app.operations.auth.sign_in_operation import SignInOperation
from app.models.users.user import UserRole


router = APIRouter(prefix="/lms")


class SignInLmsPayload(BaseModel):
    email: str
    password: str
    role: UserRole


@router.post("/sign-in", response_model=TokensSerializer)
async def sign_in(payload: SignInLmsPayload):
    if payload.role not in [UserRole.ADMIN, UserRole.TENANT, UserRole.TENANT_STAFF]:
        raise HTTPException(
            status_code=422, 
            detail="Invalid role. Must be ADMIN, TENANT, or TENANT_STAFF"
        )
    
    result = SignInOperation().execute(payload=payload.__dict__, role=payload.role)

    if result.is_success:
        return result.data["tokens"]
    else:
        raise HTTPException(status_code=422, detail=result.error_message)
