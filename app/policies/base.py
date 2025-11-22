from sqlalchemy.orm import Session

from app.models.permission import Permission
from app.models.user import User


class BasePolicies:
    def __init__(self, db: Session, current_user: User, policy_codes: list[str] = []):
        self.db = db
        self.current_user = current_user
        self.policy_codes = policy_codes
        self.enabled_policies = self._get_enabled_policies()
        self.preload_policies()

    def _get_enabled_policies(self) -> list[str]:
        results = self.db.query(Permission).filter(
            Permission.code.in_(self.policy_codes),
            Permission.is_enabled == True,
        ).all()
        
        return [result.code for result in results]

    def preload_policies(self) -> None:
        pass

