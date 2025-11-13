from datetime import datetime, timezone, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.logging import logger
from app.libs.database import with_db_session_for_class_instance
from app.libs.vietqr import GenerateQRCodeRequest
from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.schemas import order, payment
from app.services.payment_service import PaymentService, PaymentProviderEnum


class GeneratePaymentDetailsOperation:
    def __init__(self, payment_id: UUID):
        self.payment_id = payment_id
        
        self._preload()
        self._validate()
        
        logger.info(f"Payment method: {self.payment.payment_method}")

    @with_db_session_for_class_instance
    def execute(self, db: Session):
        if self.payment.payment_method == PaymentMethod.DISCOUNT_FULL and self.payment.total_amount == 0:
            return

        self.payment.status = PaymentStatus.WAITING_FOR_PAYMENT_DETAIL
        db.add(self.payment)
        db.commit()
        
        print(f"Payment method: {self.payment.payment_method}")

        transaction_id, details = self._get_payment_details(db)
        
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

    def _validate(self):
        if self.payment.status != PaymentStatus.NEW:
            raise ValueError(f"Payment {self.payment.id} cannot generate details in status {self.payment.status.value}")

    def _get_payment(self, db: Session):
        return (
            db.query(Payment)
            .filter(Payment.id == self.payment_id)
            .first()
        )

    def _get_payment_details(self, db: Session):
        if self.payment.payment_method == PaymentMethod.QR:
            return self._generate_payment_qr_code(db)

        if self.payment.payment_method == PaymentMethod.CARD:
            return self._generate_payment_card(db)
        
        raise ValueError(f"Payment method {self.payment.payment_method} is not supported")

    def _generate_payment_qr_code(self, db: Session):
        """Generate payment QR code."""
        payment_service = PaymentService(provider_name=PaymentProviderEnum.VIETQR)
        
        # Payment method details
        _ = self.payment.payment_method
        payment_method_details = self.payment.payment_method_details
        bank_code = payment_method_details.get('bank_code')
        bank_account_number = payment_method_details.get('bank_account_number')
        bank_account_name = payment_method_details.get('bank_account_name')
        
        if not bank_code or not bank_account_number or not bank_account_name:
            raise ValueError("Bank code, bank account number, and bank account name are required")
        
        # Create QR generation request
        qr_request = GenerateQRCodeRequest(
            amount=str(int(self.payment.total_amount)),
            content=str(self.payment.transaction_code),
            orderId=str(self.order.id),
            terminalCode=str(self.order.store_id),
            bankCode=bank_code,
            bankAccountNumber=bank_account_number,
            bankAccountName=bank_account_name,
        )
        
        # Generate QR code
        qr_code, transaction_id, transaction_ref_id = payment_service.generate_qr_code(request=qr_request)
        
        # Update payment with generated details
        details = {
            "qr_code": qr_code,
            "transaction_id": transaction_id,
            "transaction_ref_id": transaction_ref_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat(),
        }

        return transaction_id, details
    
    def _generate_payment_card(self, db: Session):
        pass
