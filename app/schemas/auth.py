from pydantic import BaseModel

from app.models.user import UserRole


class RegisterLMSUserRequest(BaseModel):
    email: str
    password: str
    role: UserRole
