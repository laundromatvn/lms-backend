from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.user import User, UserStatus
from app.schemas.user import CreateUserRequest


class CreateUserOperation:

    def __init__(self, db: Session, current_user: User, payload: CreateUserRequest):
        self.db = db
        self.current_user = current_user
        self.payload = payload

    def execute(self) -> User:
        is_exist = (
            self.db.query(User)
            .filter(
                or_(
                    User.phone == self.payload.phone,
                    User.email == self.payload.email,
                ),
                User.deleted_at.is_(None),
            )
            .first()
        )
        if is_exist:
            raise ValueError("User with this phone or email already exists")

        user = User(
            email=self.payload.email,
            phone=self.payload.phone,
            role=self.payload.role,
            status=UserStatus.ACTIVE,
            verified_at=func.now(),
            is_verified=True,
        )
        user.set_password(self.payload.password)

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
