from enum import Enum

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.libs.database import Base
import uuid
import datetime


class PromotionCodeStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    USED = "USED"
    EXPIRED = "EXPIRED"
    
    
class PromotionCodeValueType(str, Enum):
    AMOUNT = "AMOUNT"
    PERCENTAGE = "PERCENTAGE"


class PromotionCode(Base):
    __tablename__ = "promotion_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    code = Column(String(255), nullable=False, unique=True, index=True)
    discount = Column(Integer, nullable=False)
    expiration_date = Column(DateTime, nullable=True)
