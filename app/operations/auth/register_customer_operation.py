from typing import Dict, Any, Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.operations.base import BaseOperation, OperationResult
from app.models.users.user import User, UserRole
from app.libs.auth_manager import auth_manager
from app.utils.phone_number import is_valid_phone_format    


class RegisterCustomerOperation(BaseOperation[Dict[str, Any]]):

    def validate_input(self, *args, **kwargs) -> Optional[OperationResult[Dict[str, Any]]]:
        payload = kwargs.get("payload", {})
        
        self.phone = payload.get("phone")
        self.password = payload.get("password")

        if not self.phone:
            return OperationResult.failure("Phone is required")

        if not self.password:
            return OperationResult.failure("Password is required")

        if not is_valid_phone_format(self.phone):
            return OperationResult.failure("Invalid phone number format")

        return None

    def _execute_impl(self, *args, **kwargs) -> OperationResult[Dict[str, Any]]:
        try:
            result = auth_manager.user_repository.create_customer(
                phone=self.phone,
                password=self.password
            )
            
            if result.is_success:
                return OperationResult.success(result.data)
            else:
                return result
                
        except Exception as e:
            return OperationResult.failure(
                f"Customer registration failed: {str(e)}",
                "REGISTRATION_ERROR"
            )
