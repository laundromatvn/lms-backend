from enum import Enum
import uuid

from sqlalchemy import (
    Enum as SQLEnum,
    Column,
    String,
    DateTime,
    ForeignKey,
    Boolean,
    Integer,
    func,
    Numeric,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.libs.database import Base


class SubscriptionPlanType(str, Enum):
    RECURRING = "RECURRING"
    ONE_TIME = "ONE_TIME"


class SubscriptionPlanInterval(str, Enum):
    MONTH = "MONTH"
    YEAR = "YEAR"


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())   
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    deleted_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)

    type = Column(
        SQLEnum(SubscriptionPlanType, name="subscription_plan_type", create_type=False),
        nullable=False,
        default=SubscriptionPlanType.RECURRING,
        index=True
    )
    name = Column(String(255), nullable=False, index=True)
    description = Column(String(500), nullable=False)
    is_enabled = Column(Boolean, nullable=False, default=True)
    is_default = Column(Boolean, nullable=False, default=False)
    
    price = Column(Numeric(10, 2), nullable=False)
    interval = Column(
        SQLEnum(SubscriptionPlanInterval, name="subscription_plan_interval", create_type=False),
        nullable=True,
        default=SubscriptionPlanInterval.MONTH,
        index=True
    )
    interval_count = Column(Integer, nullable=True, default=1)
    trial_period_count = Column(Integer, nullable=True, default=0) # follow interval

    permission_group_id = Column(UUID(as_uuid=True), ForeignKey('permission_groups.id'), nullable=True, index=True)
    
    permission_group = relationship("PermissionGroup", back_populates="subscription_plans")

    def soft_delete(self, deleted_by: uuid.UUID) -> None:
        self.deleted_at = func.now()
        self.deleted_by = deleted_by
