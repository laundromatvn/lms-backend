from datetime import datetime, timezone, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.enums.vnpay import VNPAYMethodCodeEnum
from app.libs.database import with_db_session_for_class_instance
from app.libs.vnpay import CardPayment
from app.models.payment import Payment, PaymentMethod, PaymentStatus, PaymentProvider
from app.models.store import Store
from app.services.payment_service import PaymentService, PaymentProviderEnum


class GeneratePaymentDetailsOperation:
    def __init__(self, payment_id: UUID):
        self.payment_id = payment_id

        self._preload()
        self._validate()

    @with_db_session_for_class_instance
    def execute(self, db: Session):
        if (
            self.payment.payment_method == PaymentMethod.DISCOUNT_FULL
            and self.payment.total_amount == 0
        ):
            return

        self.payment.status = PaymentStatus.WAITING_FOR_PAYMENT_DETAIL
        db.add(self.payment)
        db.commit()

        transaction_id, details = self._get_payment_details()

        self.payment.details = details
        self.payment.provider_transaction_id = transaction_id
        self.payment.status = PaymentStatus.WAITING_FOR_PURCHASE
        db.add(self.payment)
        db.commit()
        db.refresh(self.payment)

        return self.payment

    @with_db_session_for_class_instance
    def _preload(self, db: Session):
        self.payment = self._get_payment(db)
        if not self.payment:
            raise ValueError(f"Payment {self.payment_id} not found")

        self.order = self.payment.order
        self.store = self.payment.store

    def _validate(self):
        if self.payment.status != PaymentStatus.NEW:
            raise ValueError(
                f"Payment {self.payment.id} cannot generate details in status {self.payment.status.value}"
            )

    def _get_payment(self, db: Session):
        return db.query(Payment).filter(Payment.id == self.payment_id).first()

    def _get_payment_details(self):
        if self.payment.payment_method == PaymentMethod.QR and self.payment.provider == PaymentProvider.VNPAY:
            return self._generate_payment_vnpay_qr()

        elif self.payment.payment_method == PaymentMethod.QR and self.payment.provider == PaymentProvider.VIET_QR:
            return self._generate_payment_vietqr_qr()

        elif self.payment.payment_method == PaymentMethod.CARD and self.payment.provider == PaymentProvider.VNPAY:
            return self._generate_payment_card()

        else:
            raise ValueError(
                f"Payment method {self.payment.payment_method} is not supported"
            )

    def _generate_payment_vnpay_qr(self):
        payment_method_details = self.payment.payment_method_details
        if not payment_method_details:
            raise ValueError("VNPAY payment method details are required")

        vnpay_cfg = {
            "merchant_code": payment_method_details.get("merchant_code"),
            "terminal_code": payment_method_details.get("terminal_code"),
            "init_secret_key": payment_method_details.get("init_secret_key"),
            "query_secret_key": payment_method_details.get("query_secret_key"),
            "ipnv3_secret_key": payment_method_details.get("ipnv3_secret_key"),
        }

        required_fields = [
            "merchant_code",
            "terminal_code",
            "init_secret_key",
            "query_secret_key",
            "ipnv3_secret_key",
        ]
        missing_fields = [
            field for field in required_fields if not vnpay_cfg.get(field)
        ]
        if missing_fields:
            raise ValueError(
                f"VNPAY payment method details missing required fields: {', '.join(missing_fields)}"
            )

        payment_service = PaymentService(
            provider_name=PaymentProviderEnum.VNPAY, cfg=vnpay_cfg
        )

        payment_request_id, qr_content, trace_id = payment_service.generate_qr_code(
            order_code=self.payment.transaction_code,
            amount=int(self.payment.total_amount),
            client_transaction_code=self.payment.transaction_code,
            user_id=str(self.order.created_by) if self.order.created_by else "",
            description=str(self.payment.transaction_code),
        )

        details = {
            "qr_code": qr_content,
            "payment_request_id": payment_request_id,
            "trace_id": trace_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (
                datetime.now(timezone.utc) + timedelta(minutes=15)
            ).isoformat(),
        }

        return payment_request_id, details

    def _generate_payment_vietqr_qr(self):
        payment_service = PaymentService(provider_name=PaymentProviderEnum.VIET_QR)

        payment_method_details = self.payment.payment_method_details
        bank_account_number = payment_method_details.get("bank_account_number")
        if not bank_account_number:
            raise ValueError("Bank account number is required")
        
        bank_account_name = payment_method_details.get("bank_account_name")
        if not bank_account_name:
            raise ValueError("Bank account name is required")

        bank_code = payment_method_details.get("bank_code")
        if not bank_code:
            raise ValueError("Bank code is required")

        qr_code, transaction_id, transaction_ref_id = (
            payment_service.generate_qr_code(
                amount=int(self.payment.total_amount),
                content=str(self.payment.transaction_code),
                order_code=str(self.order.id),
                terminalCode=str(self.order.store_id),
                bankCode=bank_code or "",
                bankAccountNumber=bank_account_number or "",
                bankAccountName=bank_account_name or "",
            )
        )

        details = {
            "qr_code": qr_code,
            "transaction_id": transaction_id,
            "transaction_ref_id": transaction_ref_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (
                datetime.now(timezone.utc) + timedelta(minutes=15)
            ).isoformat(),
        }

        return transaction_id, details

    def _generate_payment_card(self):
        cfg = self._get_vnpay_cfg(self.store)
        payment_service = PaymentService(
            provider_name=PaymentProviderEnum.VNPAY, cfg=cfg
        )

        card_payment = CardPayment(
            client_transaction_code=self.payment.transaction_code,
            amount=int(self.payment.total_amount),
            method_code=VNPAYMethodCodeEnum.CARD,
        )

        transaction_id, details = payment_service.pay_by_card(
            order_code=self.payment.transaction_code,
            total_payment_amount=int(self.payment.total_amount),
            card_payment=card_payment,
        )

        return transaction_id, details

    def _get_vnpay_cfg(self, store: Store):
        for method in store.payment_methods:
            if (
                method.get("payment_method") == PaymentMethod.CARD
                and method.get("payment_provider") == PaymentProvider.VNPAY
            ):
                return method.get("details")

        return {}

