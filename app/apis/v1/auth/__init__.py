from fastapi import APIRouter, Depends

from app.apis.v1.auth import customer
from app.serializers.users.user_serializer import UserSerializer
from app.models.users.user import User
from app.apis.deps import get_current_user


router = APIRouter(prefix="/auth")

router.include_router(customer.router)


@router.get("/me", response_model=UserSerializer)
async def get_me(user: User = Depends(get_current_user)):
    """
    Get current authenticated user's profile information.
    
    This endpoint works for all user roles (ADMIN, TENANT, TENANT_STAFF, CUSTOMER).
    
    Returns:
        UserSerializer: Current user's profile data including:
        - id: User UUID
        - email: User email (if applicable)
        - phone: User phone (if applicable)
        - role: User role
        - is_verified: Verification status
        - created_at: Account creation timestamp
        - updated_at: Last update timestamp
        - verified_at: Verification timestamp (if verified)
    """
    return user.to_dict()
