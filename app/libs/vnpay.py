from dataclasses import dataclass
import hmac, hashlib, base64
from typing import Optional, Dict, Any
import requests

from app.core.config import settings


def _hmac_sha256_base64(secret: str, message: str) -> str:
    key = secret.encode("utf-8")
    msg = message.encode("utf-8")
    mac = hmac.new(key, msg, hashlib.sha256).digest()
    return base64.b64encode(mac).decode("utf-8")


@dataclass
class CardPayment:
    """Card or Installment payment object according to VNPAY spec."""
    client_transaction_code: str
    amount: int
    method_code: str = "VNPAY_SPOS_CARD"  # or VNPAY_SPOS_INSTALLMENT
    merchant_method_code: str = ""
    card_promotion: bool = False
    voucher_card_promotion: Optional[str] = None
    buyer_name: Optional[str] = None
    buyer_phone: Optional[str] = None
    buyer_email: Optional[str] = None
    buyer_identification: Optional[str] = None
    payment_term: Optional[int] = None  # months if installment

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "methodCode": self.method_code,
            "merchantMethodCode": self.merchant_method_code or "",
            "clientTransactionCode": self.client_transaction_code,
            "amount": self.amount,
        }
        if self.card_promotion:
            data["cardPromotion"] = True
            if not self.voucher_card_promotion:
                raise ValueError("voucher_card_promotion required when cardPromotion=True")
            data["voucherCardPromotion"] = self.voucher_card_promotion
        if self.method_code == "VNPAY_SPOS_INSTALLMENT":
            data.update({
                "buyerName": self.buyer_name,
                "buyerPhone": self.buyer_phone,
                "buyerEmail": self.buyer_email,
                "buyerIdentification": self.buyer_identification,
                "paymentTerm": self.payment_term,
            })
        return data


class VnPayService:
    """Unified service for both QR and Card payments."""
    
    CREATE_ORDER_PATH = "{vnpay_base_url}/external/merchantorder"
    
    """
        cfg: VNPAYPaymentMethodDetails
            merchant_code: str
            terminal_code: str
            init_secret_key: str
            query_secret_key: str
            ipnv3_secret_key: str
    """

    def __init__(self, cfg):
        self.merchant_code = cfg.get("merchant_code")
        self.terminal_code = cfg.get("terminal_code")
        self.init_secret_key = cfg.get("init_secret_key")
        self.query_secret_key = cfg.get("query_secret_key")
        self.ipnv3_secret_key = cfg.get("ipnv3_secret_key")

        self.vnpay_base_url = settings.VNPAY_BASE_URL
        self.create_order_path = self.CREATE_ORDER_PATH.format(
            vnpay_base_url=self.vnpay_base_url,
            merchant_code=self.merchant_code,
        )
        self.success_url = "" # just for QR or Web
        self.cancel_url = "" # just for QR or Web

    def pay_by_card(
        self,
        order_code: str,
        total_payment_amount: int,
        card_payment: CardPayment,
        user_id: str = "",
        description: str = "",
    ) -> Dict[str, Any]:
        payload = self.build_card_payment_payload(
            order_code=order_code,
            total_payment_amount=total_payment_amount,
            card_payment=card_payment,
            user_id=user_id,
            description=description,
        )
        
        headers = {
            "Content-Type": "application/json",
        }

        response = requests.post(self.create_order_path, json=payload, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to create order: {response.status_code} {response.text}")
        
        """
        {
            "orderCode": "VJINST-5078",
            "paymentRequestId": "MO12522",
            "payments": {
                "card": {
                    "amount": "1000",
                    "transactionCode": "MO12522",
                    "responseCode": "200",
                    "responseMessage": "thành công",
                    "traceId": "MO12522",
                    "methodCode": "VNPAY_SPOS_CARD",
                    "clientTransactionCode": "001bc70b-5a28-48e7-9780-5b217cf2908d"
                }
            },
            "message": "Khởi tạo đơn hàng thành công",
            "code": "200"
        }
        """
        
        data = response.json() if response.status_code == 200 else {}
        
        transaction_id = response.json().get("paymentRequestId")
        transaction_details = response.json().get("payments", {}).get("card", {})

        return transaction_id, transaction_details

    def build_card_payment_payload(
        self,
        order_code: str,
        total_payment_amount: int,
        card_payment: CardPayment,
        user_id: str = "",
        description: str = "",
    ) -> Dict[str, Any]:
        """
        Build payload for VNPAY card or installment payment.
        """
        if not order_code or len(order_code) > 50:
            raise ValueError("order_code must be non-empty and ≤ 50 chars")

        payments = {"card": card_payment.to_dict()}

        payload = {
            "merchantCode": self.merchant_code,
            "terminalCode": self.terminal_code,
            "userId": user_id,
            "orderCode": order_code,
            "totalPaymentAmount": total_payment_amount,
            "description": description,
            "payments": payments,
            "cancelUrl": self.cancel_url,
            "successUrl": self.success_url,
        }

        # checksum formula (from spec):
        # "secretKey + orderCode|userId|terminalCode|merchantCode|
        # totalPaymentAmount|successUrl|cancelUrl|clientTransactionCode|
        # MerchantMethodCode|methodCode|amount"
        secret = self.init_secret_key
        fields = [
            order_code,
            user_id,
            self.terminal_code,
            self.merchant_code,
            str(total_payment_amount),
            self.success_url,
            self.cancel_url,
            card_payment.client_transaction_code,
            card_payment.merchant_method_code,
            card_payment.method_code,
            str(card_payment.amount),
        ]
        checksum_input = secret + "|".join(fields)
        payload["checksum"] = _hmac_sha256_base64(secret, checksum_input)
        return payload

    def compute_getorderdetail_checksum(
        self, payment_request_id: Optional[str], order_code: Optional[str]
    ) -> str:
        """
        Compute checksum for getorderdetail as spec:
        checksum = base64(HMAC_SHA256(querySecretKey, secret + terminalCode|merchantCode|paymentRequestId|orderCode))
        """
        secret = self.query_secret_key or self.init_secret_key
        fields = [
            self.terminal_code,
            self.merchant_code,
            payment_request_id or "",
            order_code or "",
        ]
        joined = "|".join(fields)
        checksum_input = secret + joined
        return _hmac_sha256_base64(secret, checksum_input)


