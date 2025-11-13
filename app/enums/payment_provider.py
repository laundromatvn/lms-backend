from enum import Enum


class PaymentProviderEnum(str, Enum):
    VIET_QR = "VIET_QR"
    VNPAY = "VNPAY"
    INTERNAL_PROMOTION = "INTERNAL_PROMOTION"
