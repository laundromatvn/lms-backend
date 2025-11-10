from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID
import json

from pydantic import BaseModel, Field, validator, root_validator

from app.models.order import OrderStatus, OrderDetailStatus, AddOnType
from app.models.machine import MachineType
from app.models.payment import PaymentStatus
from app.schemas.pagination import Pagination


class AddOnItem(BaseModel):
    """Schema for individual add-on item"""
    type: AddOnType = Field(..., description="Type of add-on service")
    price: Decimal = Field(..., description="Price for this add-on")
    is_default: bool = Field(..., description="Whether this add-on is included by default")
    quantity: int = Field(..., ge=1, description="Quantity of this add-on")

    @validator('price')
    def validate_price(cls, v):
        if v < 0:
            raise ValueError("Add-on price cannot be negative")
        return v


class MachineSelection(BaseModel):
    """Schema for machine selection in order creation"""
    machine_id: UUID = Field(..., description="ID of the machine to book")
    add_ons: Optional[List[AddOnItem]] = Field(None, description="Additional services or options")


class CreateOrderRequest(BaseModel):
    """Schema for creating a new order"""
    store_id: UUID = Field(..., description="ID of the store where the order is placed")
    machine_selections: List[MachineSelection] = Field(
        ..., 
        min_items=1,
        description="List of machines to book with their options"
    )

    @validator('machine_selections')
    def validate_machine_selections(cls, v):
        if not v:
            raise ValueError("At least one machine selection is required")
        
        # Check for duplicate machine IDs
        machine_ids = [selection.machine_id for selection in v]
        if len(machine_ids) != len(set(machine_ids)):
            raise ValueError("Duplicate machine selections are not allowed")
        
        return v


class CreateOrderDetailRequest(BaseModel):
    """Schema for creating a new order detail"""
    machine_id: UUID = Field(..., description="ID of the machine to book")
    add_ons: Optional[List[AddOnItem]] = Field(None, description="Additional services or options")


class UpdateOrderStatusRequest(BaseModel):
    """Schema for updating order status"""
    status: OrderStatus = Field(..., description="New order status")

    @validator('status')
    def validate_status(cls, v):
        if not isinstance(v, OrderStatus):
            try:
                v = OrderStatus(v)
            except ValueError:
                raise ValueError(f"Invalid status: {v}")
        return v


class UpdateOrderDetailStatusRequest(BaseModel):
    """Schema for updating order detail status"""
    status: OrderDetailStatus = Field(..., description="New order detail status")

    @validator('status')
    def validate_status(cls, v):
        if not isinstance(v, OrderDetailStatus):
            try:
                v = OrderDetailStatus(v)
            except ValueError:
                raise ValueError(f"Invalid status: {v}")
        return v


class ListOrderDetailQueryParams(Pagination):
    order_id: Optional[UUID] = None


class OrderDetailResponse(BaseModel):
    """Schema for order detail response"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    status: OrderDetailStatus
    machine_id: UUID
    order_id: UUID
    add_ons: Optional[List[AddOnItem]]
    price: Decimal
    machine_name: Optional[str] = None
    machine_relay_no: Optional[int] = None
    machine_type: Optional[MachineType] = None
    

    class Config:
        from_attributes = True

    @validator('add_ons', pre=True)
    def parse_add_ons(cls, v):
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return [AddOnItem(**item) for item in parsed]
                return None
            except (json.JSONDecodeError, ValueError):
                return None
        elif isinstance(v, list):
            try:
                return [AddOnItem(**item) for item in v]
            except ValueError:
                return None
        return v


class OrderResponse(BaseModel):
    """Schema for order response"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    transaction_code: str | None = None
    status: OrderStatus
    sub_total: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    total_washer: int
    total_dryer: int
    store_id: UUID
    store_name: Optional[str] = None
    promotion_summary: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class OrderDetailListResponse(BaseModel):
    """Schema for order detail list response"""
    order_details: List[OrderDetailResponse]
    total: int


class OrderSummaryResponse(BaseModel):
    """Schema for order summary (without full details)"""
    id: UUID
    created_at: datetime
    status: OrderStatus
    total_amount: Decimal
    total_washer: int
    total_dryer: int
    store_id: UUID
    store_name: Optional[str] = None

    class Config:
        from_attributes = True


class OrderFilterRequest(BaseModel):
    """Schema for filtering orders"""
    store_id: Optional[UUID] = None
    status: Optional[OrderStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None

    @validator('end_date')
    def validate_date_range(cls, v, values):
        if v and 'start_date' in values and values['start_date']:
            if v < values['start_date']:
                raise ValueError("End date must be after start date")
        return v

    @validator('max_amount')
    def validate_amount_range(cls, v, values):
        if v and 'min_amount' in values and values['min_amount']:
            if v < values['min_amount']:
                raise ValueError("Max amount must be greater than min amount")
        return v


class OrderStatsResponse(BaseModel):
    """Schema for order statistics"""
    total_orders: int
    total_revenue: Decimal
    orders_by_status: Dict[str, int]
    orders_by_store: Dict[str, int]
    average_order_value: Decimal
    total_washers_booked: int
    total_dryers_booked: int


class MachineAvailabilityRequest(BaseModel):
    """Schema for checking machine availability"""
    store_id: UUID = Field(..., description="ID of the store")
    machine_type: Optional[MachineType] = Field(None, description="Type of machine to check")
    start_time: Optional[datetime] = Field(None, description="Start time for availability check")
    end_time: Optional[datetime] = Field(None, description="End time for availability check")


class MachineAvailabilityResponse(BaseModel):
    """Schema for machine availability response"""
    machine_id: UUID
    machine_name: Optional[str]
    machine_type: MachineType
    is_available: bool
    current_status: str
    estimated_completion: Optional[datetime] = None
    base_price: Decimal


class OrderValidationError(BaseModel):
    """Schema for order validation errors"""
    field: str
    message: str
    code: str


class OrderValidationResponse(BaseModel):
    """Schema for order validation response"""
    is_valid: bool
    errors: List[OrderValidationError] = []
    warnings: List[str] = []


class OrderCancellationRequest(BaseModel):
    """Schema for order cancellation"""
    reason: Optional[str] = Field(None, max_length=500, description="Reason for cancellation")
    refund_requested: bool = Field(False, description="Whether to request a refund")

    @validator('reason')
    def validate_reason(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v


class OrderCompletionRequest(BaseModel):
    """Schema for order completion"""
    completion_notes: Optional[str] = Field(None, max_length=1000, description="Notes about order completion")
    customer_rating: Optional[int] = Field(None, ge=1, le=5, description="Customer rating (1-5)")

    @validator('completion_notes')
    def validate_completion_notes(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v


class ListOrderQueryParams(Pagination):
    tenant_id: Optional[UUID] = None
    store_id: Optional[UUID] = None
    status: Optional[OrderStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    payment_status: Optional[PaymentStatus] = None
    query: Optional[str] = None
    order_by: Optional[str] = None
    order_direction: Optional[str] = None
