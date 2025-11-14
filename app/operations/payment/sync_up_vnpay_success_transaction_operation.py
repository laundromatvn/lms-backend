from sqlalchemy.orm import Session

from app.libs.database import with_db_session_for_class_instance
from app.models.payment import Payment, PaymentProvider, PaymentStatus
from app.models.order import Order, OrderStatus
from app.operations.order.order_operation import OrderOperation
from app.schemas.vnpay import VNPAYSyncUpSuccessTransactionRequest


class SyncUpVnPaySuccessTransactionOperation:
    def __init__(self, request: VNPAYSyncUpSuccessTransactionRequest):
        self.request = request

    @with_db_session_for_class_instance
    def execute(self, db: Session):
        self._preload(db)
        self._validate_request(db)

        self.payment.update_status(PaymentStatus.SUCCESS)
        db.add(self.payment)
        db.commit()
        db.refresh(self.payment)

        OrderOperation.update_order_status(self.order.id, OrderStatus.IN_PROGRESS)

        return self.payment

    def _preload(self, db: Session):
        self.payment = self._get_payment(db)
        if not self.payment:
            raise ValueError(f"Payment with transaction code {self.request.orderCode} not found")
        
        self.order = self._get_order(db)
        if not self.order:
            raise ValueError(f"Order with payment ID {self.payment.id} not found")

    def _get_payment(self, db: Session):
        return (
            db.query(Payment)
            .filter(
                Payment.transaction_code == self.request.orderCode,
                Payment.provider == PaymentProvider.VNPAY,
                Payment.deleted_at.is_(None),
            )
            .first()
        )

    def _get_order(self, db: Session):
        return (
            db.query(Order)
            .filter(
                Order.id == self.payment.order_id,
                Order.deleted_at.is_(None),
            )
            .first()
        )

    def _validate_request(self, db: Session):
        # TODO: Validate request + Verify checksum
        return True
