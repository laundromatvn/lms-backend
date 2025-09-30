from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator

from app.models.payment import (
    PaymentStatus, 
    PaymentProvider
)


# Payment Schemas
class InitializePaymentRequest(BaseModel):
    """Request schema for initializing a payment"""
    order_id: UUID = Field(..., description="ID of the order to pay for")
    store_id: UUID = Field(..., description="ID of the store")
    tenant_id: UUID = Field(..., description="ID of the tenant")
    total_amount: Decimal = Field(..., description="Total payment amount")
    provider: PaymentProvider = Field(default=PaymentProvider.VIET_QR, description="Payment provider")

    @validator('total_amount')
    def validate_total_amount(cls, v):
        if v <= 0:
            raise ValueError("Total amount must be greater than 0")
        return v


class PaymentResponse(BaseModel):
    """Response schema for payment details"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    order_id: UUID
    status: PaymentStatus
    details: Optional[dict] = None
    store_id: UUID
    tenant_id: UUID
    total_amount: Decimal
    provider: PaymentProvider
    provider_transaction_id: Optional[str] = None

    class Config:
        from_attributes = True
