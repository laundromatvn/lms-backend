from typing import Dict
from sqlalchemy.orm import Session

from app.models.permission import Permission
from app.models.user import User


class BasePolicies:

    required_permissions: list[str] = []

    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user
        self.enabled_policies = self._get_enabled_policies()
        self.preload_policies()

    def _get_enabled_policies(self) -> list[str]:
        results = self.db.query(Permission).filter(
            Permission.code.in_(self.required_permissions),
            Permission.is_enabled == True,
        ).all()
        
        return [result.code for result in results]

    def preload_policies(self) -> None:
        pass
    
    def access(self) -> Dict[str, bool]:
        return {}

