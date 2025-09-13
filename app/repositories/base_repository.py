"""
Base repository class for all model repositories.

This module provides a comprehensive base repository class that can be inherited
by child repositories to implement common database operations with proper error
handling, logging, and transaction management.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union, Tuple
from contextlib import contextmanager
from datetime import datetime

from sqlalchemy import and_, or_, desc, asc, func, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, Query
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from app.core.logging import get_logger
from app.core.database import get_session, with_db_session
from app.operations.base import OperationResult, OperationStatus

# Type variables for generic repository
ModelType = TypeVar('ModelType')
CreateSchemaType = TypeVar('CreateSchemaType')
UpdateSchemaType = TypeVar('UpdateSchemaType')


class RepositoryError(Exception):
    """Base exception for repository operations."""
    pass


class NotFoundError(RepositoryError):
    """Raised when a record is not found."""
    pass


class DuplicateError(RepositoryError):
    """Raised when trying to create a duplicate record."""
    pass


class ValidationError(RepositoryError):
    """Raised when validation fails."""
    pass


class BaseRepository(ABC, Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base repository class providing common database operations.
    
    This class provides a foundation for implementing repositories with:
    - CRUD operations (Create, Read, Update, Delete)
    - Advanced querying capabilities
    - Transaction management
    - Error handling and logging
    - Pagination support
    - Bulk operations
    
    Child repositories should inherit from this class and specify the model type.
    
    Example:
        class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
            def __init__(self):
                super().__init__(User)
    """
    
    def __init__(self, model: Type[ModelType]):
        """
        Initialize the base repository.
        
        Args:
            model: The SQLAlchemy model class this repository manages
        """
        self.model = model
        self.logger = get_logger().bind(repository=self.__class__.__name__)
    
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
                user = session.query(self.model).filter(self.model.id == user_id).first()
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
    def with_session(func):
        """
        Static decorator method to automatically manage database sessions for repository methods.
        
        This decorator automatically provides a database session as the first
        argument to the decorated method and handles session cleanup.
        
        The decorated method should accept 'session' as its first parameter
        after 'self'.
        
        Args:
            func: The method to decorate
            
        Returns:
            Callable: The decorated method
            
        Example:
            @BaseRepository.with_session
            def get_by_id(self, session: Session, id: str):
                return session.query(self.model).filter(self.model.id == id).first()
        """
        return with_db_session(func)
    
    # ==================== CREATE OPERATIONS ====================
    
    @with_session
    def create(self, session: Session, obj_in: CreateSchemaType, **kwargs) -> OperationResult[ModelType]:
        """
        Create a new record.
        
        Args:
            session: Database session
            obj_in: Data for creating the record
            **kwargs: Additional fields to set on the model
            
        Returns:
            OperationResult: Success with created model or failure with error message
        """
        try:
            # Convert schema to dict if it's a Pydantic model
            if hasattr(obj_in, 'dict'):
                obj_data = obj_in.dict()
            elif hasattr(obj_in, 'model_dump'):
                obj_data = obj_in.model_dump()
            else:
                obj_data = obj_in
            
            # Merge with additional kwargs
            obj_data.update(kwargs)
            
            # Create model instance
            db_obj = self.model(**obj_data)
            session.add(db_obj)
            session.flush()  # Flush to get the ID without committing
            session.refresh(db_obj)
            
            self.logger.info("Record created successfully", model=self.model.__name__, id=getattr(db_obj, 'id', None))
            return OperationResult.success(db_obj)
            
        except IntegrityError as e:
            session.rollback()
            self.logger.error("Integrity error during creation", error=str(e))
            
            # Handle specific integrity errors
            if hasattr(e.orig, 'pgcode'):
                if e.orig.pgcode == '23505':  # Unique violation
                    return OperationResult.failure("Record with this data already exists", "DUPLICATE_ERROR")
                elif e.orig.pgcode == '23503':  # Foreign key violation
                    return OperationResult.failure("Referenced record does not exist", "FOREIGN_KEY_ERROR")
            
            return OperationResult.failure(f"Database integrity error: {str(e)}", "INTEGRITY_ERROR")
            
        except Exception as e:
            session.rollback()
            self.logger.error("Unexpected error during creation", error=str(e))
            return OperationResult.failure(f"Failed to create record: {str(e)}", "CREATE_ERROR")
    
    @with_session
    def create_many(self, session: Session, objs_in: List[CreateSchemaType], **kwargs) -> OperationResult[List[ModelType]]:
        """
        Create multiple records in a single transaction.
        
        Args:
            session: Database session
            objs_in: List of data for creating records
            **kwargs: Additional fields to set on all models
            
        Returns:
            OperationResult: Success with list of created models or failure with error message
        """
        try:
            created_objects = []
            
            for obj_in in objs_in:
                # Convert schema to dict if it's a Pydantic model
                if hasattr(obj_in, 'dict'):
                    obj_data = obj_in.dict()
                elif hasattr(obj_in, 'model_dump'):
                    obj_data = obj_in.model_dump()
                else:
                    obj_data = obj_in
                
                # Merge with additional kwargs
                obj_data.update(kwargs)
                
                # Create model instance
                db_obj = self.model(**obj_data)
                session.add(db_obj)
                created_objects.append(db_obj)
            
            session.flush()  # Flush to get IDs without committing
            
            # Refresh all objects to get their IDs
            for obj in created_objects:
                session.refresh(obj)
            
            self.logger.info("Multiple records created successfully", 
                           model=self.model.__name__, count=len(created_objects))
            return OperationResult.success(created_objects)
            
        except IntegrityError as e:
            session.rollback()
            self.logger.error("Integrity error during bulk creation", error=str(e))
            return OperationResult.failure(f"Database integrity error during bulk creation: {str(e)}", "BULK_CREATE_ERROR")
            
        except Exception as e:
            session.rollback()
            self.logger.error("Unexpected error during bulk creation", error=str(e))
            return OperationResult.failure(f"Failed to create records: {str(e)}", "BULK_CREATE_ERROR")
    
    # ==================== READ OPERATIONS ====================
    
    @with_session
    def get(self, session: Session, id: Any) -> OperationResult[ModelType]:
        """
        Get a single record by ID.
        
        Args:
            session: Database session
            id: Primary key value
            
        Returns:
            OperationResult: Success with model or failure if not found
        """
        try:
            db_obj = session.query(self.model).filter(self.model.id == id).first()
            
            if not db_obj:
                return OperationResult.failure(f"Record with id {id} not found", "NOT_FOUND")
            
            return OperationResult.success(db_obj)
            
        except Exception as e:
            self.logger.error("Error getting record by id", id=id, error=str(e))
            return OperationResult.failure(f"Failed to get record: {str(e)}", "GET_ERROR")
    
    @with_session
    def get_multi(
        self, 
        session: Session, 
        skip: int = 0, 
        limit: int = 100,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ) -> OperationResult[List[ModelType]]:
        """
        Get multiple records with pagination.
        
        Args:
            session: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            order_by: Field to order by (defaults to id)
            order_desc: Whether to order in descending order
            
        Returns:
            OperationResult: Success with list of models
        """
        try:
            query = session.query(self.model)
            
            # Apply ordering
            if order_by:
                order_field = getattr(self.model, order_by, None)
                if order_field:
                    if order_desc:
                        query = query.order_by(desc(order_field))
                    else:
                        query = query.order_by(asc(order_field))
            else:
                # Default ordering by id
                if order_desc:
                    query = query.order_by(desc(self.model.id))
                else:
                    query = query.order_by(asc(self.model.id))
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            
            db_objs = query.all()
            return OperationResult.success(db_objs)
            
        except Exception as e:
            self.logger.error("Error getting multiple records", error=str(e))
            return OperationResult.failure(f"Failed to get records: {str(e)}", "GET_MULTI_ERROR")
    
    @with_session
    def get_by_field(self, session: Session, field_name: str, value: Any) -> OperationResult[ModelType]:
        """
        Get a single record by a specific field.
        
        Args:
            session: Database session
            field_name: Name of the field to filter by
            value: Value to match
            
        Returns:
            OperationResult: Success with model or failure if not found
        """
        try:
            field = getattr(self.model, field_name, None)
            if not field:
                return OperationResult.failure(f"Field '{field_name}' does not exist on model", "INVALID_FIELD")
            
            db_obj = session.query(self.model).filter(field == value).first()
            
            if not db_obj:
                return OperationResult.failure(f"Record with {field_name}={value} not found", "NOT_FOUND")
            
            return OperationResult.success(db_obj)
            
        except Exception as e:
            self.logger.error("Error getting record by field", field=field_name, value=value, error=str(e))
            return OperationResult.failure(f"Failed to get record by field: {str(e)}", "GET_BY_FIELD_ERROR")
    
    @with_session
    def get_multi_by_field(self, session: Session, field_name: str, value: Any) -> OperationResult[List[ModelType]]:
        """
        Get multiple records by a specific field.
        
        Args:
            session: Database session
            field_name: Name of the field to filter by
            value: Value to match
            
        Returns:
            OperationResult: Success with list of models
        """
        try:
            field = getattr(self.model, field_name, None)
            if not field:
                return OperationResult.failure(f"Field '{field_name}' does not exist on model", "INVALID_FIELD")
            
            db_objs = session.query(self.model).filter(field == value).all()
            return OperationResult.success(db_objs)
            
        except Exception as e:
            self.logger.error("Error getting records by field", field=field_name, value=value, error=str(e))
            return OperationResult.failure(f"Failed to get records by field: {str(e)}", "GET_MULTI_BY_FIELD_ERROR")
    
    @with_session
    def count(self, session: Session, **filters) -> OperationResult[int]:
        """
        Count records matching the given filters.
        
        Args:
            session: Database session
            **filters: Field-value pairs to filter by
            
        Returns:
            OperationResult: Success with count
        """
        try:
            query = session.query(self.model)
            
            # Apply filters
            for field_name, value in filters.items():
                field = getattr(self.model, field_name, None)
                if field:
                    query = query.filter(field == value)
            
            count = query.count()
            return OperationResult.success(count)
            
        except Exception as e:
            self.logger.error("Error counting records", filters=filters, error=str(e))
            return OperationResult.failure(f"Failed to count records: {str(e)}", "COUNT_ERROR")
    
    @with_session
    def exists(self, session: Session, **filters) -> OperationResult[bool]:
        """
        Check if any record exists matching the given filters.
        
        Args:
            session: Database session
            **filters: Field-value pairs to filter by
            
        Returns:
            OperationResult: Success with boolean indicating existence
        """
        try:
            query = session.query(self.model)
            
            # Apply filters
            for field_name, value in filters.items():
                field = getattr(self.model, field_name, None)
                if field:
                    query = query.filter(field == value)
            
            exists = session.query(query.exists()).scalar()
            return OperationResult.success(bool(exists))
            
        except Exception as e:
            self.logger.error("Error checking existence", filters=filters, error=str(e))
            return OperationResult.failure(f"Failed to check existence: {str(e)}", "EXISTS_ERROR")
    
    # ==================== UPDATE OPERATIONS ====================
    
    @with_session
    def update(self, session: Session, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]) -> OperationResult[ModelType]:
        """
        Update an existing record.
        
        Args:
            session: Database session
            db_obj: The model instance to update
            obj_in: Data for updating the record
            
        Returns:
            OperationResult: Success with updated model or failure with error message
        """
        try:
            # Convert schema to dict if it's a Pydantic model
            if hasattr(obj_in, 'dict'):
                update_data = obj_in.dict(exclude_unset=True)
            elif hasattr(obj_in, 'model_dump'):
                update_data = obj_in.model_dump(exclude_unset=True)
            else:
                update_data = obj_in
            
            # Update fields
            for field, value in update_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)
            
            # Update timestamp if the model has updated_at field
            if hasattr(db_obj, 'updated_at'):
                setattr(db_obj, 'updated_at', datetime.utcnow())
            
            session.flush()
            session.refresh(db_obj)
            
            self.logger.info("Record updated successfully", model=self.model.__name__, id=getattr(db_obj, 'id', None))
            return OperationResult.success(db_obj)
            
        except IntegrityError as e:
            session.rollback()
            self.logger.error("Integrity error during update", error=str(e))
            return OperationResult.failure(f"Database integrity error during update: {str(e)}", "UPDATE_INTEGRITY_ERROR")
            
        except Exception as e:
            session.rollback()
            self.logger.error("Unexpected error during update", error=str(e))
            return OperationResult.failure(f"Failed to update record: {str(e)}", "UPDATE_ERROR")
    
    @with_session
    def update_by_id(self, session: Session, id: Any, obj_in: Union[UpdateSchemaType, Dict[str, Any]]) -> OperationResult[ModelType]:
        """
        Update a record by ID.
        
        Args:
            session: Database session
            id: Primary key value
            obj_in: Data for updating the record
            
        Returns:
            OperationResult: Success with updated model or failure with error message
        """
        try:
            # First get the record
            get_result = self.get(session, id)
            if get_result.is_failure:
                return get_result
            
            # Update the record
            return self.update(session, get_result.data, obj_in)
            
        except Exception as e:
            self.logger.error("Error updating record by id", id=id, error=str(e))
            return OperationResult.failure(f"Failed to update record by id: {str(e)}", "UPDATE_BY_ID_ERROR")
    
    # ==================== DELETE OPERATIONS ====================
    
    @with_session
    def remove(self, session: Session, id: Any) -> OperationResult[ModelType]:
        """
        Delete a record by ID.
        
        Args:
            session: Database session
            id: Primary key value
            
        Returns:
            OperationResult: Success with deleted model or failure with error message
        """
        try:
            # First get the record
            get_result = self.get(session, id)
            if get_result.is_failure:
                return get_result
            
            db_obj = get_result.data
            session.delete(db_obj)
            session.flush()
            
            self.logger.info("Record deleted successfully", model=self.model.__name__, id=id)
            return OperationResult.success(db_obj)
            
        except Exception as e:
            session.rollback()
            self.logger.error("Error deleting record", id=id, error=str(e))
            return OperationResult.failure(f"Failed to delete record: {str(e)}", "DELETE_ERROR")
    
    @with_session
    def remove_multi(self, session: Session, ids: List[Any]) -> OperationResult[List[ModelType]]:
        """
        Delete multiple records by IDs.
        
        Args:
            session: Database session
            ids: List of primary key values
            
        Returns:
            OperationResult: Success with list of deleted models or failure with error message
        """
        try:
            deleted_objects = []
            
            for id in ids:
                get_result = self.get(session, id)
                if get_result.is_success:
                    db_obj = get_result.data
                    session.delete(db_obj)
                    deleted_objects.append(db_obj)
            
            session.flush()
            
            self.logger.info("Multiple records deleted successfully", 
                           model=self.model.__name__, count=len(deleted_objects))
            return OperationResult.success(deleted_objects)
            
        except Exception as e:
            session.rollback()
            self.logger.error("Error deleting multiple records", ids=ids, error=str(e))
            return OperationResult.failure(f"Failed to delete records: {str(e)}", "BULK_DELETE_ERROR")
    
    # ==================== ADVANCED QUERY OPERATIONS ====================
    
    @with_session
    def filter(
        self, 
        session: Session, 
        filters: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ) -> OperationResult[List[ModelType]]:
        """
        Filter records with complex conditions.
        
        Args:
            session: Database session
            filters: Dictionary of field-value pairs to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return
            order_by: Field to order by
            order_desc: Whether to order in descending order
            
        Returns:
            OperationResult: Success with list of filtered models
        """
        try:
            query = session.query(self.model)
            
            # Apply filters
            for field_name, value in filters.items():
                field = getattr(self.model, field_name, None)
                if field:
                    if isinstance(value, list):
                        # Handle IN queries
                        query = query.filter(field.in_(value))
                    elif isinstance(value, dict):
                        # Handle range queries (e.g., {'gte': 10, 'lte': 20})
                        if 'gte' in value:
                            query = query.filter(field >= value['gte'])
                        if 'lte' in value:
                            query = query.filter(field <= value['lte'])
                        if 'gt' in value:
                            query = query.filter(field > value['gt'])
                        if 'lt' in value:
                            query = query.filter(field < value['lt'])
                        if 'like' in value:
                            query = query.filter(field.like(f"%{value['like']}%"))
                    else:
                        # Exact match
                        query = query.filter(field == value)
            
            # Apply ordering
            if order_by:
                order_field = getattr(self.model, order_by, None)
                if order_field:
                    if order_desc:
                        query = query.order_by(desc(order_field))
                    else:
                        query = query.order_by(asc(order_field))
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            
            db_objs = query.all()
            return OperationResult.success(db_objs)
            
        except Exception as e:
            self.logger.error("Error filtering records", filters=filters, error=str(e))
            return OperationResult.failure(f"Failed to filter records: {str(e)}", "FILTER_ERROR")
    
    @with_session
    def search(
        self, 
        session: Session, 
        search_term: str,
        search_fields: List[str],
        skip: int = 0,
        limit: int = 100
    ) -> OperationResult[List[ModelType]]:
        """
        Search records across multiple fields.
        
        Args:
            session: Database session
            search_term: Term to search for
            search_fields: List of field names to search in
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            OperationResult: Success with list of matching models
        """
        try:
            query = session.query(self.model)
            
            # Build search conditions
            search_conditions = []
            for field_name in search_fields:
                field = getattr(self.model, field_name, None)
                if field:
                    search_conditions.append(field.like(f"%{search_term}%"))
            
            if search_conditions:
                query = query.filter(or_(*search_conditions))
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            
            db_objs = query.all()
            return OperationResult.success(db_objs)
            
        except Exception as e:
            self.logger.error("Error searching records", search_term=search_term, error=str(e))
            return OperationResult.failure(f"Failed to search records: {str(e)}", "SEARCH_ERROR")
    
    # ==================== UTILITY METHODS ====================
    
    def get_query(self, session: Session) -> Query:
        """
        Get a base query object for custom queries.
        
        Args:
            session: Database session
            
        Returns:
            Query: SQLAlchemy query object
        """
        return session.query(self.model)
    
    @with_session
    def execute_raw_query(self, session: Session, query: str, params: Optional[Dict[str, Any]] = None) -> OperationResult[List[Dict[str, Any]]]:
        """
        Execute a raw SQL query.
        
        Args:
            session: Database session
            query: Raw SQL query string
            params: Query parameters
            
        Returns:
            OperationResult: Success with query results
        """
        try:
            result = session.execute(text(query), params or {})
            
            # Convert result to list of dictionaries
            columns = result.keys()
            rows = result.fetchall()
            
            data = [dict(zip(columns, row)) for row in rows]
            return OperationResult.success(data)
            
        except Exception as e:
            self.logger.error("Error executing raw query", query=query, error=str(e))
            return OperationResult.failure(f"Failed to execute raw query: {str(e)}", "RAW_QUERY_ERROR")
    
    @with_session
    def get_stats(self, session: Session, group_by: Optional[str] = None) -> OperationResult[Dict[str, Any]]:
        """
        Get basic statistics for the model.
        
        Args:
            session: Database session
            group_by: Optional field to group statistics by
            
        Returns:
            OperationResult: Success with statistics dictionary
        """
        try:
            stats = {}
            
            # Total count
            total_count = session.query(self.model).count()
            stats['total_count'] = total_count
            
            # Group by statistics if specified
            if group_by:
                group_field = getattr(self.model, group_by, None)
                if group_field:
                    group_stats = session.query(
                        group_field,
                        func.count(self.model.id).label('count')
                    ).group_by(group_field).all()
                    
                    stats['group_by'] = {
                        'field': group_by,
                        'groups': [{'value': row[0], 'count': row[1]} for row in group_stats]
                    }
            
            return OperationResult.success(stats)
            
        except Exception as e:
            self.logger.error("Error getting statistics", error=str(e))
            return OperationResult.failure(f"Failed to get statistics: {str(e)}", "STATS_ERROR")
