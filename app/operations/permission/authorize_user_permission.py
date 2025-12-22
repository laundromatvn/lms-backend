from sqlalchemy.orm import Session

from app.libs.database import with_db_session_classmethod
from app.models.user import User
from app.operations.permission.get_user_permissions import GetUserPermissionsOperation


class AuthorizeUserPermissionOperation:
    
    @with_db_session_classmethod
    def execute(self, db: Session, user: User, permissions: list[str]) -> bool:
        # TODO: Add cache logic
        user_permissions = GetUserPermissionsOperation().execute(db, user)

        is_authorized = all(permission in user_permissions for permission in permissions)

        return is_authorized
