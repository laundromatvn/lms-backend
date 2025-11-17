from sqlalchemy.orm import Session

from app.libs.database import with_db_session_classmethod
from app.models.user import User
from app.schemas.user import (
    CreateUserRequest,
    UpdateUserRequest,
    ResetPasswordRequest,
)

class UserOperation:
    
    @classmethod
    @with_db_session_classmethod
    def create(
        cls,
        db: Session,
        current_user: User,
        request: CreateUserRequest,
    ) -> User:
        user = User(
            email=request.email,
            phone=request.phone,
            role=request.role,
            status=request.status,
        )
        user.set_password(request.password)
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user

    @classmethod
    @with_db_session_classmethod
    def get(
        cls,
        db: Session,
        current_user: User,
        user_id: str,
    ) -> User:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        if not cls._have_permission(current_user, user):
            raise PermissionError("You are not allowed to get this user")

        return user

    @classmethod
    @with_db_session_classmethod
    def update_partially(
        cls,
        db: Session,
        current_user: User,
        user_id: str,
        request: UpdateUserRequest,
    ) -> User:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        if not cls._have_permission(current_user, user):
            raise PermissionError("You are not allowed to update this user")
        
        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "password":
                user.set_password(value)
                continue
            else:
                setattr(user, field, value)

        db.commit()
        db.refresh(user)

        return user
    
    @classmethod
    @with_db_session_classmethod
    def reset_password(
        cls,
        db: Session,
        current_user: User,
        user_id: str,
        request: ResetPasswordRequest,
    ) -> User:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        if not cls._have_permission(current_user, user):
            raise PermissionError("You are not allowed to reset password for this user")
        
        user.set_password(request.password)
        db.commit()
        db.refresh(user)

        return user

    @classmethod
    @with_db_session_classmethod
    def _have_permission(
        cls,
        db: Session,
        current_user: User,
        user: User,
    ) -> bool:
        # TODO: Implement permission check
        
        return True
