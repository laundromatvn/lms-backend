from dataclasses import dataclass
import hmac, hashlib, base64
from typing import Optional, Dict, Any, Tuple
import requests
import unidecode
import re

from app.core.config import settings
from app.core.logging import logger


def _hmac_sha256_base64(secret: str, message: str) -> str:
    key = secret.encode("utf-8")
    msg = message.encode("utf-8")
    mac = hmac.new(key, msg, hashlib.sha256).digest()
    return base64.b64encode(mac).decode("utf-8")


def _clean_qr_description(desc: str) -> str:
    """
    VNPAY QR requires:
    - <= 19 characters
    - no diacritics
    - only A-Z0-9- and space
    """
    if not desc:
        return ""

    # Remove Vietnamese diacritics
    desc = unidecode.unidecode(desc)

    # Only keep allowed chars
    desc = re.sub(r"[^A-Za-z0-9\- ]", "", desc)

    # Limit length 19
    return desc[:19]


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


@dataclass
class QrPayment:
    client_transaction_code: str
    amount: int
    method_code: str = "VNPAY_QRCODE"
    merchant_method_code: str = ""
    qr_image_type: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "methodCode": self.method_code,
            "merchantMethodCode": self.merchant_method_code or "",
            "clientTransactionCode": self.client_transaction_code,
            "amount": self.amount,
            "qrImageType": self.qr_image_type,
        }


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
        )
        self.success_url = ""
        self.cancel_url = ""

    def pay_by_qr(
        self,
        order_code: str,
        total_payment_amount: int,
        qr_payment: QrPayment,
        user_id: str = "",
        description: str = "",
    ) -> Tuple[Optional[str], Optional[str], Dict[str, Any]]:
        description = _clean_qr_description(description)

        payload = self.build_qr_payment_payload(
            order_code=order_code,
            total_payment_amount=total_payment_amount,
            qr_payment=qr_payment,
            user_id=user_id,
            description=description,
        )

        response = requests.post(
            self.create_order_path,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        data = response.json()

        # Check for explicit error indicators first
        if data.get("errorCode") or data.get("error"):
            error_msg = data.get("errorMessage") or data.get("error") or "Unknown VNPAY error"
            logger.error(
                "[VNPAY] QR API returned error",
                error_code=data.get("errorCode"),
                error_message=error_msg,
                response_data=data
            )
            raise ValueError(f"VNPAY API error: {error_msg}")

        response_code = data.get("code")
        if response_code is not None:
            try:
                code_int = int(response_code) if isinstance(response_code, str) else response_code
                if code_int != 200:
                    logger.error(
                        "[VNPAY] QR creation failed",
                        error_code=code_int,
                        message=data.get("message"),
                    )
                    raise ValueError(f"VNPAY QR Error {code_int}: {data.get('message')}")
            except (ValueError, TypeError):
                logger.warning(
                    "[VNPAY] QR response has non-numeric code",
                    code=response_code,
                    message=data.get("message"),
                )

        # Extract QR data
        qr_block = data.get("payments", {}).get("qr", {})

        payment_request_id = data.get("paymentRequestId") or qr_block.get("transactionCode")
        qr_content = qr_block.get("qrContent")

        if not payment_request_id or not qr_content:
            logger.error(
                "[VNPAY] QR missing paymentRequestId or qrContent",
                response=data
            )
            raise ValueError("VNPAY QR response missing required fields")

        return payment_request_id, qr_content, qr_block

    def build_qr_payment_payload(
        self,
        order_code: str,
        total_payment_amount: int,
        qr_payment: QrPayment,
        user_id: str,
        description: str,
    ) -> Dict[str, Any]:

        payments = {"qr": qr_payment.to_dict()}

        payload = {
            "merchantCode": self.merchant_code,
            "terminalCode": self.terminal_code,
            "userId": user_id,
            "orderCode": order_code,
            "totalPaymentAmount": total_payment_amount,
            "description": description,
            "payments": payments,
            "successUrl": self.success_url,
            "cancelUrl": self.cancel_url,
        }

        checksum_input = (
            f"{self.init_secret_key}"
            f"{order_code}|{user_id}|{self.terminal_code}|{self.merchant_code}|"
            f"{total_payment_amount}|{self.success_url}|{self.cancel_url}|"
            f"{qr_payment.client_transaction_code}|{qr_payment.merchant_method_code}|"
            f"{qr_payment.method_code}|{qr_payment.amount}"
        )

        payload["checksum"] = _hmac_sha256_base64(self.init_secret_key, checksum_input)

        return payload

    def pay_by_card(
        self,
        order_code: str,
        total_payment_amount: int,
        card_payment: CardPayment,
        user_id: str = "",
        description: str = "",
    ) -> Tuple[Optional[str], Dict[str, Any]]:
        payload = self.build_card_payment_payload(
            order_code=order_code,
            total_payment_amount=total_payment_amount,
            card_payment=card_payment,
            user_id=user_id,
            description=description,
        )

        headers = {"Content-Type": "application/json"}

        response = requests.post(self.create_order_path, json=payload, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to create order: {response.status_code} {response.text}")

        data = response.json()
        transaction_id = data.get("paymentRequestId") or data.get("payments", {}).get("card", {}).get("transactionCode")
        transaction_details = data.get("payments", {}).get("card", {})

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
            card_payment.merchant_method_code or "",
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

