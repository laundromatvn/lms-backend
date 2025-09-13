from typing import Dict, Any, Optional

from app.operations.base import BaseOperation, OperationResult
from app.models.users.user import UserRole
from app.libs.auth_manager import auth_manager
from app.utils.phone_number import is_valid_phone_format


class SignInOperation(BaseOperation[Dict[str, Any]]):

    def validate_input(self, *args, **kwargs) -> Optional[OperationResult[Dict[str, Any]]]:
        payload = kwargs.get("payload", {})
        
        self.phone = payload.get("phone")
        self.email = payload.get("email")
        self.password = payload.get("password")
        self.role = kwargs.get("role")

        if not self.password:
            return OperationResult.failure("Password is required")

        if self.role == UserRole.CUSTOMER:
            if not self.phone:
                return OperationResult.failure("Phone is required for customer")
            if not is_valid_phone_format(self.phone):
                return OperationResult.failure("Invalid phone number format")
        else:
            if not self.email:
                return OperationResult.failure("Email is required for this role")
            if '@' not in self.email:
                return OperationResult.failure("Invalid email format")

        return None

    def _execute_impl(self, *args, **kwargs) -> OperationResult[Dict[str, Any]]:
        try:
            if self.role == UserRole.CUSTOMER:
                identifier = self.phone
            else:
                identifier = self.email
            
            result = auth_manager.sign_in_user(
                identifier=identifier,
                password=self.password,
                role=self.role
            )
            
            return result
            
        except Exception as e:
            return OperationResult.failure(
                f"Sign-in operation failed: {str(e)}",
                "SIGN_IN_OPERATION_ERROR"
            )
