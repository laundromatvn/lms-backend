"""
Authentication manager for shared authentication actions across operations, APIs, and other components.

This module provides a centralized authentication service that consolidates:
- User authentication (sign-in)
- Token creation and verification
- Password management
- User session management
- Role-based access control

Usage Examples:

1. In Operations:
    from app.libs.auth_manager import auth_manager
    
    # Sign in user
    result = auth_manager.sign_in_user("user@example.com", "password", UserRole.CUSTOMER)
    if result.is_success:
        user_data = result.data["user"]
        tokens = result.data["tokens"]
    
    # Verify token
    result = auth_manager.verify_access_token(token)
    if result.is_success:
        user = result.data

2. In APIs:
    from app.libs.auth_manager import auth_manager
    
    # In dependency injection
    def get_current_user(token: str = Depends(oauth2_scheme)):
        result = auth_manager.verify_access_token(token)
        if result.is_failure:
            raise HTTPException(status_code=401, detail=result.error_message)
        return result.data

3. In Services:
    from app.libs.auth_manager import auth_manager
    
    # Check permissions
    result = auth_manager.check_user_permissions(user, required_role=UserRole.ADMIN)
    if result.is_failure:
        raise PermissionError(result.error_message)
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
from uuid import UUID

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    verify_token
)
from app.core.config import settings
from app.models.users.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.operations.base import OperationResult
from app.core.logging import logger
from app.utils.phone_number import normalize_phone_for_authentication, is_valid_phone_format


class AuthManager:
    """
    Centralized authentication manager for shared authentication actions.
    
    This class provides a unified interface for authentication operations
    that can be used across operations, APIs, and other components.
    """
    
    def __init__(self):
        """Initialize the authentication manager."""
        self.user_repository = UserRepository()
        self.logger = logger.bind(component="auth_manager")
    
    def authenticate_user(
        self, 
        identifier: str, 
        password: str, 
        role: Optional[UserRole] = None
    ) -> OperationResult[User]:
        """
        Authenticate a user with email/phone and password.
        
        Args:
            identifier: Email or phone number
            password: Plain text password
            role: Optional role filter for authentication
            
        Returns:
            OperationResult containing the authenticated user or error
        """
        try:
            # Normalize identifier for authentication based on role
            normalized_identifier = self._normalize_identifier(identifier, role)
            
            # Use repository's authenticate method with normalized identifier
            result = self.user_repository.authenticate_user(normalized_identifier, password)
            
            if result.is_failure:
                self.logger.warning("Authentication failed", 
                                  identifier=identifier,
                                  normalized_identifier=normalized_identifier,
                                  error=result.error_message)
                return result
            
            user = result.data
            
            # Check role if specified
            if role and user.role != role:
                self.logger.warning("Role mismatch during authentication", 
                                  user_id=str(user.id),
                                  expected_role=role.value,
                                  actual_role=user.role.value)
                return OperationResult.failure(
                    f"Access denied for role: {user.role.value}",
                    "ROLE_MISMATCH"
                )
            
            self.logger.info("User authenticated successfully", 
                           user_id=str(user.id),
                           role=user.role.value)
            return OperationResult.success(user)
            
        except Exception as e:
            self.logger.error("Authentication error", 
                            identifier=identifier, 
                            error=str(e))
            return OperationResult.failure(
                f"Authentication failed: {str(e)}",
                "AUTH_ERROR"
            )
    
    def create_tokens(self, user: User) -> OperationResult[Dict[str, str]]:
        """
        Create access and refresh tokens for a user.
        
        Args:
            user: User object to create tokens for
            
        Returns:
            OperationResult containing token dictionary
        """
        try:
            # Create access token
            access_token_data = {
                "sub": str(user.id),
                "role": user.role.value,
                "email": user.email,
                "phone": user.phone
            }
            
            access_token = create_access_token(access_token_data)
            
            # Create refresh token with longer expiration
            refresh_token_data = {
                "sub": str(user.id),
                "type": "refresh"
            }
            
            refresh_token = create_access_token(
                refresh_token_data,
                expires_delta=timedelta(days=settings.jwt_refresh_token_expire_days)
            )
            
            tokens = {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": settings.jwt_access_token_expire_minutes * 60
            }
            
            self.logger.info("Tokens created successfully", 
                           user_id=str(user.id))
            return OperationResult.success(tokens)
            
        except Exception as e:
            self.logger.error("Token creation error", 
                            user_id=str(user.id), 
                            error=str(e))
            return OperationResult.failure(
                f"Token creation failed: {str(e)}",
                "TOKEN_CREATION_ERROR"
            )
    
    def verify_access_token(self, token: str) -> OperationResult[User]:
        """
        Verify an access token and return the associated user.
        
        Args:
            token: JWT access token
            
        Returns:
            OperationResult containing the user or error
        """
        try:
            # Verify token and get user ID
            user_id = verify_token(token)
            if not user_id:
                return OperationResult.failure(
                    "Invalid or expired token",
                    "INVALID_TOKEN"
                )
            
            # Get user from database
            user_result = self.user_repository.get(user_id)
            if user_result.is_failure:
                return OperationResult.failure(
                    "User not found",
                    "USER_NOT_FOUND"
                )
            
            user = user_result.data
            
            # Check if user is still verified
            if not user.is_verified:
                return OperationResult.failure(
                    "User account is not verified",
                    "ACCOUNT_NOT_VERIFIED"
                )
            
            self.logger.debug("Token verified successfully", 
                            user_id=str(user.id))
            return OperationResult.success(user)
            
        except Exception as e:
            self.logger.error("Token verification error", 
                            error=str(e))
            return OperationResult.failure(
                f"Token verification failed: {str(e)}",
                "TOKEN_VERIFICATION_ERROR"
            )
    
    def refresh_access_token(self, refresh_token: str) -> OperationResult[Dict[str, str]]:
        """
        Refresh an access token using a refresh token.
        
        Args:
            refresh_token: JWT refresh token
            
        Returns:
            OperationResult containing new tokens
        """
        try:
            # Verify refresh token
            user_id = verify_token(refresh_token)
            if not user_id:
                return OperationResult.failure(
                    "Invalid or expired refresh token",
                    "INVALID_REFRESH_TOKEN"
                )
            
            # Get user from database
            user_result = self.user_repository.get(user_id)
            if user_result.is_failure:
                return OperationResult.failure(
                    "User not found",
                    "USER_NOT_FOUND"
                )
            
            user = user_result.data
            
            # Check if user is still verified
            if not user.is_verified:
                return OperationResult.failure(
                    "User account is not verified",
                    "ACCOUNT_NOT_VERIFIED"
                )
            
            # Create new tokens
            return self.create_tokens(user)
            
        except Exception as e:
            self.logger.error("Token refresh error", 
                            error=str(e))
            return OperationResult.failure(
                f"Token refresh failed: {str(e)}",
                "TOKEN_REFRESH_ERROR"
            )
    
    def sign_in_user(
        self, 
        identifier: str, 
        password: str, 
        role: Optional[UserRole] = None
    ) -> OperationResult[Dict[str, Any]]:
        """
        Complete sign-in process: authenticate user and create tokens.
        
        Args:
            identifier: Email or phone number
            password: Plain text password
            role: Optional role filter
            
        Returns:
            OperationResult containing user data and tokens
        """
        try:
            # Authenticate user
            auth_result = self.authenticate_user(identifier, password, role)
            if auth_result.is_failure:
                return auth_result
            
            user = auth_result.data
            
            # Create tokens
            tokens_result = self.create_tokens(user)
            if tokens_result.is_failure:
                return tokens_result
            
            # Combine user data and tokens
            sign_in_data = {
                "user": user.to_dict(),
                "tokens": tokens_result.data
            }
            
            self.logger.info("User signed in successfully", 
                           user_id=str(user.id),
                           role=user.role.value)
            return OperationResult.success(sign_in_data)
            
        except Exception as e:
            self.logger.error("Sign-in error", 
                            identifier=identifier, 
                            error=str(e))
            return OperationResult.failure(
                f"Sign-in failed: {str(e)}",
                "SIGN_IN_ERROR"
            )
    
    def change_password(
        self, 
        user_id: str, 
        current_password: str, 
        new_password: str
    ) -> OperationResult[User]:
        """
        Change a user's password.
        
        Args:
            user_id: User ID
            current_password: Current plain text password
            new_password: New plain text password
            
        Returns:
            OperationResult containing updated user
        """
        try:
            # Get user
            user_result = self.user_repository.get(user_id)
            if user_result.is_failure:
                return OperationResult.failure(
                    "User not found",
                    "USER_NOT_FOUND"
                )
            
            user = user_result.data
            
            # Verify current password
            if not user.verify_password(current_password):
                return OperationResult.failure(
                    "Current password is incorrect",
                    "INVALID_CURRENT_PASSWORD"
                )
            
            # Update password
            update_result = self.user_repository.update_password(user_id, new_password)
            if update_result.is_failure:
                return update_result
            
            self.logger.info("Password changed successfully", 
                           user_id=str(user.id))
            return update_result
            
        except Exception as e:
            self.logger.error("Password change error", 
                            user_id=user_id, 
                            error=str(e))
            return OperationResult.failure(
                f"Password change failed: {str(e)}",
                "PASSWORD_CHANGE_ERROR"
            )
    
    def verify_user_account(self, user_id: str) -> OperationResult[User]:
        """
        Verify a user account.
        
        Args:
            user_id: User ID to verify
            
        Returns:
            OperationResult containing verified user
        """
        try:
            result = self.user_repository.verify_user(user_id)
            if result.is_success:
                self.logger.info("User account verified", 
                               user_id=user_id)
            return result
            
        except Exception as e:
            self.logger.error("User verification error", 
                            user_id=user_id, 
                            error=str(e))
            return OperationResult.failure(
                f"User verification failed: {str(e)}",
                "USER_VERIFICATION_ERROR"
            )
    
    def check_user_permissions(
        self, 
        user: User, 
        required_role: Optional[UserRole] = None,
        required_roles: Optional[list[UserRole]] = None
    ) -> OperationResult[bool]:
        """
        Check if a user has required permissions.
        
        Args:
            user: User object
            required_role: Single required role
            required_roles: List of acceptable roles
            
        Returns:
            OperationResult containing permission check result
        """
        try:
            if required_role:
                has_permission = user.role == required_role
            elif required_roles:
                has_permission = user.role in required_roles
            else:
                has_permission = True
            
            if not has_permission:
                self.logger.warning("Permission denied", 
                                  user_id=str(user.id),
                                  user_role=user.role.value,
                                  required_role=required_role.value if required_role else None,
                                  required_roles=[r.value for r in required_roles] if required_roles else None)
                return OperationResult.failure(
                    f"Insufficient permissions. Required: {required_role.value if required_role else required_roles}",
                    "INSUFFICIENT_PERMISSIONS"
                )
            
            return OperationResult.success(True)
            
        except Exception as e:
            self.logger.error("Permission check error", 
                            user_id=str(user.id), 
                            error=str(e))
            return OperationResult.failure(
                f"Permission check failed: {str(e)}",
                "PERMISSION_CHECK_ERROR"
            )
    
    def get_user_by_token(self, token: str) -> OperationResult[User]:
        """
        Get user from token (alias for verify_access_token for API compatibility).
        
        Args:
            token: JWT access token
            
        Returns:
            OperationResult containing the user or error
        """
        return self.verify_access_token(token)
    
    def _normalize_identifier(self, identifier: str, role: Optional[UserRole] = None) -> str:
        """
        Normalize identifier for authentication based on role.
        
        Args:
            identifier: Email or phone number
            role: User role to determine expected identifier type
            
        Returns:
            Normalized identifier string
            
        Raises:
            ValueError: If identifier format is invalid for the role
        """
        if not identifier:
            raise ValueError("Identifier cannot be empty")
        
        identifier = identifier.strip()
        
        if role == UserRole.CUSTOMER:
            # For customers, expect phone number
            try:
                return normalize_phone_for_authentication(identifier)
            except ValueError as e:
                raise ValueError(f"Invalid phone number format: {str(e)}")
        else:
            # For other roles, expect email
            identifier = identifier.lower()
            if '@' not in identifier:
                raise ValueError("Invalid email format")
            return identifier


# Global instance for easy access
auth_manager = AuthManager()
