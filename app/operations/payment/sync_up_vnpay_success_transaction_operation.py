from sqlalchemy.orm import Session

from app.libs.database import with_db_session_for_class_instance
from app.models.payment import Payment, PaymentProvider, PaymentStatus
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

        return self.payment

    def _preload(self, db: Session):
        self.payment = self._get_payment(db)
        if not self.payment:
            raise ValueError(f"Payment with transaction code {self.request.orderCode} not found")

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

    def _validate_request(self, db: Session):
        # TODO: Validate request + Verify checksum
        return True
