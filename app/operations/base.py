"""
Base operation class for all operations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Generic, Optional, TypeVar, Union, Callable
from enum import Enum
from contextlib import contextmanager

from sqlalchemy.orm import Session

from app.core.logging import logger
from app.core.database import get_session, with_db_session

T = TypeVar('T')


class OperationStatus(Enum):
    """Status of an operation execution."""
    SUCCESS = "success"
    FAILURE = "failure"


@dataclass
class OperationResult(Generic[T]):
    """Result of an operation execution."""
    status: OperationStatus
    data: Optional[T] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    @property
    def is_success(self) -> bool:
        """Check if the operation was successful."""
        return self.status == OperationStatus.SUCCESS

    @property
    def is_failure(self) -> bool:
        """Check if the operation failed."""
        return self.status == OperationStatus.FAILURE


    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "status": self.status.value,
            "data": self.data,
            "error_message": self.error_message,
            "error_code": self.error_code,
            "metadata": self.metadata,
        }

    @classmethod
    def success(cls, data: Optional[T] = None, metadata: Optional[Dict[str, Any]] = None) -> 'OperationResult[T]':
        """Create a successful result."""
        return cls(
            status=OperationStatus.SUCCESS,
            data=data,
            metadata=metadata
        )

    @classmethod
    def failure(
        cls, 
        error_message: str, 
        error_code: Optional[str] = None, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'OperationResult[T]':
        """Create a failure result."""
        return cls(
            status=OperationStatus.FAILURE,
            error_message=error_message,
            error_code=error_code,
            metadata=metadata
        )


class BaseOperation(ABC, Generic[T]):
    """
    Base operation class for all operations.
    
    This class provides a foundation for implementing operations with:
    - Structured success/failure results
    - Logging support
    - Error handling
    - Input validation
    """

    def __init__(self, operation_name: Optional[str] = None):
        """
        Initialize the base operation.
        
        Args:
            operation_name: Optional name for the operation (defaults to class name)
        """
        self.operation_name = operation_name or self.__class__.__name__
        self.logger = logger.bind(operation=self.operation_name)

    @contextmanager
    def get_db_session(self) -> Session:
        """
        Get a database session with automatic cleanup.
        
        This context manager provides a database session that is automatically
        closed when exiting the context. It also handles rollback on exceptions.
        
        Yields:
            Session: A SQLAlchemy database session
            
        Example:
            with self.get_db_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                # session is automatically closed and committed/rolled back
        """
        session = get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error("Database session error", error=str(e))
            raise
        finally:
            session.close()

    @staticmethod
    def with_session(func: Callable) -> Callable:
        """
        Static decorator method to automatically manage database sessions for operation methods.
        
        This decorator automatically provides a database session as the first
        argument to the decorated method and handles session cleanup.
        
        The decorated method should accept 'session' as its first parameter
        after 'self'.
        
        Args:
            func: The method to decorate
            
        Returns:
            Callable: The decorated method
            
        Example:
            @BaseOperation.with_session
            def _execute_impl(self, session: Session, *args, **kwargs):
                user = session.query(User).filter(User.id == user_id).first()
                return OperationResult.success(user)
        """
        return with_db_session(func)

    @abstractmethod
    def _execute_impl(self, *args, **kwargs) -> OperationResult[T]:
        """
        Implement the actual operation logic.
        
        Returns:
            OperationResult: The result of the operation
        """
        raise NotImplementedError

    def validate_input(self, *args, **kwargs) -> Optional[OperationResult[T]]:
        """
        Validate input parameters before execution.
        
        Override this method in child classes to add input validation.
        
        Returns:
            OperationResult: None if validation passes, or a failure result if validation fails
        """
        return None

    def execute(self, *args, **kwargs) -> OperationResult[T]:
        """
        Execute the operation with proper error handling and logging.
        
        Returns:
            OperationResult: The result of the operation
        """
        self.logger.info("Starting operation execution")

        try:
            # Validate input
            validation_result = self.validate_input(*args, **kwargs)
            if validation_result is not None:
                self.logger.warning("Input validation failed", result=validation_result.to_dict())
                return validation_result

            # Execute the operation
            result = self._execute_impl(*args, **kwargs)

            # Log the result
            if result.is_success:
                self.logger.info("Operation completed successfully", result=result.to_dict())
            else:
                self.logger.error("Operation failed", result=result.to_dict())

            return result

        except Exception as e:
            self.logger.error("Operation execution failed with exception", error=str(e), exc_info=True)

            return OperationResult.failure(
                error_message=str(e),
                error_code="UNEXPECTED_ERROR",
                metadata={"exception_type": type(e).__name__}
            )
