from enum import Enum

from app.libs.vietqr import VietQR, GenerateQRCodeRequest
from app.libs.vnpay import VnPayService, QrPayment


class PaymentProviderEnum(str, Enum):
    VIET_QR = "VIET_QR"
    VNPAY = "VNPAY"


class PaymentService:
    def __init__(self, provider_name: str = PaymentProviderEnum.VIET_QR, **kwargs):
        self.provider_name = provider_name
        self.provider = self._get_provider(provider_name, **kwargs)
        
    def _get_provider(self, provider_name: str, **kwargs):
        if provider_name == PaymentProviderEnum.VIET_QR:
            return VietQR(**kwargs)
        
        elif provider_name == PaymentProviderEnum.VNPAY:
            cfg = kwargs.get("cfg")
            if not cfg:
                raise ValueError("VNPAY provider requires cfg dict")
            return VnPayService(cfg=cfg)

        raise ValueError(f"Provider {provider_name} not found")

    # ---------------------------------------------------------
    #                UNIFIED QR GENERATION
    # ---------------------------------------------------------
    def generate_qr_code(
        self,
        order_code: str,
        amount: int,
        **kwargs
    ) -> tuple[str, str, str]:
        """
        Generate QR code.

        VietQR returns:
            (qrCodeBase64, transactionId, transactionRefId)

        VNPAY returns:
            (paymentRequestId, qrContent, traceId or transactionCode)
        """

        # -------------------------
        # VIETQR IMPLEMENTATION
        # -------------------------
        if self.provider_name == PaymentProviderEnum.VIET_QR:
            request = GenerateQRCodeRequest(
                amount=str(amount),
                content=kwargs["content"],
                orderId=order_code,
                terminalCode=kwargs["terminalCode"],
                bankCode=kwargs["bankCode"],
                bankAccountNumber=kwargs["bankAccountNumber"],
                bankAccountName=kwargs["bankAccountName"],
            )
            return self.provider.generate_qr_code(request)

        # -------------------------
        # VNPAY IMPLEMENTATION
        # -------------------------
        if self.provider_name == PaymentProviderEnum.VNPAY:
            client_transaction_code = kwargs.get("client_transaction_code")
            if not client_transaction_code:
                raise ValueError("client_transaction_code is required for VNPAY QR payment")

            qr_payment = QrPayment(
                client_transaction_code=client_transaction_code,
                amount=amount,
                qr_image_type=kwargs.get("qr_image_type", 0),
            )

            payment_request_id, qr_content, details = self.provider.pay_by_qr(
                order_code=order_code,
                total_payment_amount=amount,
                qr_payment=qr_payment,
                user_id=kwargs.get("user_id", ""),
                description=kwargs.get("description", ""),
            )

            trace_id = details.get("traceId") or details.get("transactionCode")

            return payment_request_id, qr_content, trace_id

        raise ValueError("Unsupported QR provider")

    # ---------------------------------------------------------
    #             CARD PAYMENT (VNPAY ONLY)
    # ---------------------------------------------------------
    def pay_by_card(self, *args, **kwargs):
        if self.provider_name != PaymentProviderEnum.VNPAY:
            raise ValueError("Card payment only supported by VNPAY")
        return self.provider.pay_by_card(*args, **kwargs)

