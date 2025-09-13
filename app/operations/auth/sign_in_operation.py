"""
Sign-in operation implementation using the auth manager.
"""

from typing import Dict, Any, Optional

from app.operations.base import BaseOperation, OperationResult
from app.models.users.user import UserRole
from app.libs.auth_manager import auth_manager
from app.utils.phone_number import is_valid_phone_format


class SignInOperation(BaseOperation[Dict[str, Any]]):
    """
    Operation for user sign-in with authentication and token creation.
    """

    def validate_input(self, *args, **kwargs) -> Optional[OperationResult[Dict[str, Any]]]:
        payload = kwargs.get("payload", {})
        
        self.identifier = payload.get("identifier") or payload.get("email") or payload.get("phone")
        self.password = payload.get("password")
        self.role = kwargs.get("role")

        if not self.identifier:
            return OperationResult.failure("Email or phone is required")

        if not self.password:
            return OperationResult.failure("Password is required")

        # Validate phone number format if it's not an email
        if '@' not in self.identifier and not is_valid_phone_format(self.identifier):
            return OperationResult.failure("Invalid phone number format")

        return None

    def _execute_impl(self, *args, **kwargs) -> OperationResult[Dict[str, Any]]:
        try:
            # Use auth manager for sign-in
            result = auth_manager.sign_in_user(
                identifier=self.identifier,
                password=self.password,
                role=self.role
            )
            
            return result
            
        except Exception as e:
            return OperationResult.failure(
                f"Sign-in operation failed: {str(e)}",
                "SIGN_IN_OPERATION_ERROR"
            )
