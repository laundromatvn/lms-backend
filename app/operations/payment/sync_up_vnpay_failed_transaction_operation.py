from sqlalchemy.orm import Session

from app.libs.database import with_db_session_for_class_instance
from app.models.payment import Payment, PaymentProvider, PaymentStatus
from app.models.order import Order, OrderStatus
from app.schemas.vnpay import VNPAYIpnRequest
from app.operations.order.order_operation import OrderOperation


class SyncUpVnPayFailedTransactionOperation:
    def __init__(self, request: VNPAYIpnRequest):
        self.request = request

    @with_db_session_for_class_instance
    def execute(self, db: Session):
        self._preload(db)
        self._validate_request()

        # idempotency guard
        if self.payment.status == PaymentStatus.FAILED:
            return self.payment

        # update payment
        self.payment.update_status(PaymentStatus.FAILED)
        db.add(self.payment)
        db.commit()
        db.refresh(self.payment)

        # update order
        OrderOperation.update_order_status(
            self.order.id,
            OrderStatus.PAYMENT_FAILED
        )

        return self.payment

    def _preload(self, db: Session):
        # Prefer provider transaction code (unique)
        self.payment = (
            db.query(Payment)
            .filter(
                Payment.provider_transaction_id == self.request.transactionCode,
                Payment.provider == PaymentProvider.VNPAY,
                Payment.deleted_at.is_(None),
            )
            .first()
        )

        # fallback to internal transaction code if needed
        if not self.payment:
            self.payment = (
                db.query(Payment)
                .filter(
                    Payment.transaction_code == self.request.clientTransactionCode,
                    Payment.provider == PaymentProvider.VNPAY,
                    Payment.deleted_at.is_(None),
                )
                .first()
            )

        if not self.payment:
            raise ValueError(
                f"Payment not found: providerTransactionId={self.request.transactionCode}, internalTransactionCode={self.request.clientTransactionCode}"
            )

        self.order = (
            db.query(Order)
            .filter(
                Order.id == self.payment.order_id,
                Order.deleted_at.is_(None),
            )
            .first()
        )

        if not self.order:
            raise ValueError(f"Order for payment ID {self.payment.id} not found")

    def _validate_request(self):
        # TODO: Add checksum verification here (HMAC SHA256)
        return True

