import math
from typing import TypeVar, Generic, List
from pydantic import BaseModel, Field

T = TypeVar('T')


class Pagination(BaseModel):
    """Base pagination parameters for query endpoints"""
    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    page_size: int = Field(default=10, ge=1, le=1000, description="Number of items per page")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response schema"""
    page: int
    page_size: int
    total: int
    total_pages: int
    data: List[T]
    
    class Config:
        # This allows the generic type to be properly serialized
        arbitrary_types_allowed = True
