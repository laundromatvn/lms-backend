"""
Customer registration operation implementation.
"""

from typing import Dict, Any, Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.operations.base import BaseOperation, OperationResult
from app.models.users.user import User, UserRole    


class RegisterCustomerOperation(BaseOperation[Dict[str, Any]]):
    """
    Operation for registering a new customer.
    Can accept parameters via payload dict or individual keyword arguments.
    """

    def validate_input(self, *args, **kwargs) -> Optional[OperationResult[Dict[str, Any]]]:
        payload = kwargs.get("payload", {})
        
        self.phone = payload.get("phone")
        self.password = payload.get("password")

        if not self.phone:
            return OperationResult.failure("Phone is required")

        if not self.password:
            return OperationResult.failure("Password is required")

        return None

    @BaseOperation.with_session
    def _execute_impl(self, session: Session, *args, **kwargs) -> OperationResult[Dict[str, Any]]:
        try:
            user = User(
                phone=self.phone,
                password=User.set_password(self.password),
                role=UserRole.CUSTOMER,
                is_verified=True,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            return OperationResult.success(user)
        except IntegrityError as e:
            session.rollback()

            if hasattr(e.orig, 'pgcode') and e.orig.pgcode == '23505':
                return OperationResult.failure("Phone number already exists")
            else:
                return OperationResult.failure(f"Database integrity error: {str(e)}")
