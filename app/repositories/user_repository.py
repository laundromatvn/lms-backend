
from typing import Any, Dict, List
from sqlalchemy import func

from app.repositories.base_repository import BaseRepository
from app.models.users.user import User, UserRole
from app.operations.base import OperationResult
from app.utils.phone_number import normalize_phone_for_authentication


class UserRepository(BaseRepository[User, Dict[str, Any], Dict[str, Any]]):

    def __init__(self):
        super().__init__(User)
    
    def get_by_email(self, email: str) -> OperationResult[User]:
        return self.get_by_field("email", email)
    
    def get_by_phone(self, phone: str) -> OperationResult[User]:
        # Normalize phone number before lookup
        try:
            normalized_phone = normalize_phone_for_authentication(phone)
            return self.get_by_field("phone", normalized_phone)
        except ValueError:
            return OperationResult.failure("Invalid phone number format", "INVALID_PHONE")
    
    def get_by_role(self, role: UserRole) -> OperationResult[List[User]]:
        return self.get_multi_by_field("role", role)
    
    def get_verified_users(self, verified: bool = True) -> OperationResult[List[User]]:
        return self.get_multi_by_field("is_verified", verified)
    
    def get_users_by_role_and_verification(
        self, 
        role: UserRole, 
        verified: bool = True
    ) -> OperationResult[List[User]]:
        with self.get_db_session() as session:
            try:
                users = session.query(self.model).filter(
                    self.model.role == role,
                    self.model.is_verified == verified
                ).all()
                
                return OperationResult.success(users)
                
            except Exception as e:
                self.logger.error("Error getting users by role and verification", 
                                role=role.value, verified=verified, error=str(e))
                return OperationResult.failure(f"Failed to get users: {str(e)}", "QUERY_ERROR")
    
    def create_customer(self, phone: str, password: str, **kwargs) -> OperationResult[User]:
        # Normalize phone number before creating user
        try:
            normalized_phone = normalize_phone_for_authentication(phone)
        except ValueError as e:
            return OperationResult.failure(f"Invalid phone number format: {str(e)}", "INVALID_PHONE")
        
        user_data = {
            "phone": normalized_phone,
            "password": User.set_password(password),
            "role": UserRole.CUSTOMER,
            "is_verified": True,
            **kwargs
        }
        
        return self.create(user_data)
    
    def create_admin(self, email: str, password: str, **kwargs) -> OperationResult[User]:
        user_data = {
            "email": email,
            "password": User.set_password(password),
            "role": UserRole.ADMIN,
            "is_verified": True,
            **kwargs
        }
        
        return self.create(user_data)
    
    def create_tenant(self, email: str, password: str, **kwargs) -> OperationResult[User]:
        user_data = {
            "email": email,
            "password": User.set_password(password),
            "role": UserRole.TENANT,
            "is_verified": False,
            **kwargs
        }
        
        return self.create(user_data)
    
    def create_tenant_staff(self, email: str, password: str, **kwargs) -> OperationResult[User]:
        user_data = {
            "email": email,
            "password": User.set_password(password),
            "role": UserRole.TENANT_STAFF,
            "is_verified": False,
            **kwargs
        }
        
        return self.create(user_data)

    def verify_user(self, user_id: str) -> OperationResult[User]:
        update_data = {
            "is_verified": True,
            "verified_at": "now"
        }
        
        result = self.update_by_id(user_id, update_data)
        if result.is_success:
            result.data.verify_user()
        
        return result
    
    def update_password(self, user_id: str, new_password: str) -> OperationResult[User]:
        update_data = {
            "password": User.set_password(new_password)
        }
        
        return self.update_by_id(user_id, update_data)
    
    def update_role(self, user_id: str, new_role: UserRole) -> OperationResult[User]:
        update_data = {"role": new_role}
        return self.update_by_id(user_id, update_data)

    def authenticate_user(self, identifier: str, password: str) -> OperationResult[User]:
        user_result = self.get_by_email(identifier)
        if user_result.is_failure:
            user_result = self.get_by_phone(identifier)
        
        if user_result.is_failure:
            return OperationResult.failure("Invalid credentials", "AUTH_FAILED")
        
        user = user_result.data
        
        if not user.verify_password(password):
            return OperationResult.failure("Invalid credentials", "AUTH_FAILED")
        
        if not user.is_verified:
            return OperationResult.failure("User account is not verified", "ACCOUNT_NOT_VERIFIED")
        
        return OperationResult.success(user)

    def check_email_exists(self, email: str) -> OperationResult[bool]:
        return self.exists(email=email)
    
    def check_phone_exists(self, phone: str) -> OperationResult[bool]:
        # Normalize phone number before checking existence
        try:
            normalized_phone = normalize_phone_for_authentication(phone)
            return self.exists(phone=normalized_phone)
        except ValueError:
            return OperationResult.failure("Invalid phone number format", "INVALID_PHONE")

    def get_user_stats(self) -> OperationResult[Dict[str, Any]]:
        with self.get_db_session() as session:
            try:
                stats = {}
                
                total_count = session.query(self.model).count()
                stats['total_users'] = total_count
                
                role_stats = session.query(
                    self.model.role,
                    func.count(self.model.id).label('count')
                ).group_by(self.model.role).all()
                
                stats['by_role'] = {
                    role.value: count for role, count in role_stats
                }
                
                verified_count = session.query(self.model).filter(
                    self.model.is_verified == True
                ).count()
                
                stats['verification'] = {
                    'verified': verified_count,
                    'unverified': total_count - verified_count
                }
                
                role_verification_stats = session.query(
                    self.model.role,
                    self.model.is_verified,
                    func.count(self.model.id).label('count')
                ).group_by(self.model.role, self.model.is_verified).all()
                
                stats['by_role_and_verification'] = {}
                for role, verified, count in role_verification_stats:
                    if role.value not in stats['by_role_and_verification']:
                        stats['by_role_and_verification'][role.value] = {}
                    stats['by_role_and_verification'][role.value][str(verified)] = count
                
                return OperationResult.success(stats)
                
            except Exception as e:
                self.logger.error("Error getting user statistics", error=str(e))
                return OperationResult.failure(f"Failed to get user statistics: {str(e)}", "STATS_ERROR")

    def bulk_verify_users(self, user_ids: List[str]) -> OperationResult[List[User]]:
        with self.get_db_session() as session:
            try:
                updated_users = []
                
                for user_id in user_ids:
                    user_result = self.get(session, user_id)
                    if user_result.is_success:
                        user = user_result.data
                        user.verify_user()
                        updated_users.append(user)
                
                session.flush()
                
                self.logger.info("Bulk user verification completed", 
                               count=len(updated_users))
                return OperationResult.success(updated_users)
                
            except Exception as e:
                session.rollback()
                self.logger.error("Error in bulk user verification", error=str(e))
                return OperationResult.failure(f"Failed to bulk verify users: {str(e)}", "BULK_VERIFY_ERROR")
    
    def bulk_update_role(self, user_ids: List[str], new_role: UserRole) -> OperationResult[List[User]]:
        with self.get_db_session() as session:
            try:
                updated_users = []
                
                for user_id in user_ids:
                    user_result = self.get(session, user_id)
                    if user_result.is_success:
                        user = user_result.data
                        user.role = new_role
                        updated_users.append(user)
                
                session.flush()
                
                self.logger.info("Bulk role update completed", 
                               role=new_role.value, count=len(updated_users))
                return OperationResult.success(updated_users)
                
            except Exception as e:
                session.rollback()
                self.logger.error("Error in bulk role update", error=str(e))
                return OperationResult.failure(f"Failed to bulk update roles: {str(e)}", "BULK_ROLE_UPDATE_ERROR")
