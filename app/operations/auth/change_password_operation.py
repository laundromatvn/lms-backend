"""
Change password operation implementation using the auth manager.
"""

from typing import Dict, Any, Optional

from app.operations.base import BaseOperation, OperationResult
from app.models.users.user import User
from app.libs.auth_manager import auth_manager


class ChangePasswordOperation(BaseOperation[User]):
    """
    Operation for changing user password.
    """

    def validate_input(self, *args, **kwargs) -> Optional[OperationResult[User]]:
        payload = kwargs.get("payload", {})
        
        self.user_id = payload.get("user_id") or kwargs.get("user_id")
        self.current_password = payload.get("current_password")
        self.new_password = payload.get("new_password")

        if not self.user_id:
            return OperationResult.failure("User ID is required")

        if not self.current_password:
            return OperationResult.failure("Current password is required")

        if not self.new_password:
            return OperationResult.failure("New password is required")

        if len(self.new_password) < 6:
            return OperationResult.failure("New password must be at least 6 characters long")

        return None

    def _execute_impl(self, *args, **kwargs) -> OperationResult[User]:
        try:
            # Use auth manager for password change
            result = auth_manager.change_password(
                user_id=self.user_id,
                current_password=self.current_password,
                new_password=self.new_password
            )
            
            return result
            
        except Exception as e:
            return OperationResult.failure(
                f"Change password operation failed: {str(e)}",
                "CHANGE_PASSWORD_OPERATION_ERROR"
            )
