"""
Get user from token operation implementation using the auth manager.
"""

from typing import Dict, Any, Optional

from app.operations.base import BaseOperation, OperationResult
from app.models.users.user import User
from app.libs.auth_manager import auth_manager


class GetUserFromTokenOperation(BaseOperation[User]):
    """
    Operation for getting user from JWT token.
    """

    def validate_input(self, *args, **kwargs) -> Optional[OperationResult[User]]:
        self.token = kwargs.get("token")

        if not self.token:
            return OperationResult.failure("Token is required")

        return None

    def _execute_impl(self, *args, **kwargs) -> OperationResult[User]:
        try:
            # Use auth manager for token verification
            result = auth_manager.verify_access_token(self.token)
            
            return result
            
        except Exception as e:
            return OperationResult.failure(
                f"Get user from token operation failed: {str(e)}",
                "GET_USER_FROM_TOKEN_ERROR"
            )
