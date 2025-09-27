from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from app.libs.database import with_db_session_classmethod
from app.models.user import User
from app.utils.security import jwt
from app.schemas.auth import SignInRequest


class SignInOperation:

    @classmethod
    @with_db_session_classmethod
    def execute(cls, db: Session, request: SignInRequest) -> tuple[str, str]:
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            raise NoResultFound("User not found")

        if not user.verify_password(request.password):
            raise NoResultFound("Invalid password")

        payload = {
            "user_id": str(user.id),
        }
        access_token = jwt.create_access_token(payload)
        refresh_token = jwt.create_refresh_token(payload)
        
        return access_token, refresh_token