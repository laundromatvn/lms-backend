from app.libs.vietqr import VietQR


class PaymentService:
    def __init__(self, provider_name: str = "vietqr"):
        self.provider = self._get_provider(provider_name)
        
    def _get_provider(self, provider_name: str):
        if provider_name == "vietqr":
            return VietQR()
        else:
            raise ValueError(f"Provider {provider_name} not found")

    def generate_qr_code(self, *args, **kwargs) -> tuple[str, str, str]:
        return self.provider.generate_qr_code(*args, **kwargs)
