from enum import Enum

from app.libs.vietqr import VietQR


class PaymentProviderEnum(str, Enum):
    VIETQR = "vietqr"


class PaymentService:
    def __init__(self, provider_name: str = PaymentProviderEnum.VIETQR):
        self.provider = self._get_provider(provider_name)
        
    def _get_provider(self, provider_name: str):
        if provider_name == PaymentProviderEnum.VIETQR:
            return VietQR()
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
