from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.logging import logger
from app.libs.database import with_db_session_classmethod
from app.models.user import User, UserStatus
from app.schemas.auth import RegisterLMSUserRequest


class RegisterLMSUserOperation:

    @classmethod
    @with_db_session_classmethod
    def execute(cls, db: Session, request: RegisterLMSUserRequest) -> User:
        if db.query(User).filter(User.email == request.email).first():
            raise IntegrityError("Email already exists")

        user = User(
            email=request.email,
            role=request.role,
            status=UserStatus.WAITING_FOR_APPROVAL,
        )
        user.set_password(request.password)
        db.add(user)
        db.commit()
        db.refresh(user)

        return user
