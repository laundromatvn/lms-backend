from enum import Enum

from app.libs.vietqr import VietQR
from app.libs.vnpay import VnPayService


class PaymentProviderEnum(str, Enum):
    VIETQR = "VIETQR"
    VNPAY = "VNPAY"


class PaymentService:
    def __init__(self, provider_name: str = PaymentProviderEnum.VIETQR, **kwargs):
        self.provider = self._get_provider(provider_name, **kwargs)
        
    def _get_provider(self, provider_name: str, **kwargs):
        if provider_name == PaymentProviderEnum.VIETQR:
            return VietQR(**kwargs)
        elif provider_name == PaymentProviderEnum.VNPAY:
            return VnPayService(cfg=kwargs.get("cfg"))
        else:
            raise ValueError(f"Provider {provider_name} not found")

    def generate_qr_code(self, *args, **kwargs) -> tuple[str, str, str]:
        """
        Generate QR code for payment.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
            
        Returns:
            Depends on the provider and payment method
        """
        return self.provider.generate_qr_code(*args, **kwargs)
    
    def pay_by_card(self, *args, **kwargs):
        return self.provider.pay_by_card(*args, **kwargs)
