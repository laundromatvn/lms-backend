from datetime import timedelta
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.libs.database import with_db_session_classmethod
from app.models.payment import Payment, PaymentStatus


class SyncUpTimeoutPaymentOperation:
    
    PAYMENT_TIMEOUT_MINUTES = 5

    @classmethod
    @with_db_session_classmethod
    def execute(cls, db: Session):
        timeout_payments = cls.__get_timeout_payments(db)
        if not timeout_payments:
            logger.info("No timeout payments found")
            return
        
        logger.info(f"Found {len(timeout_payments)} timeout payments")
        
        for payment in timeout_payments:
            payment.update_status(PaymentStatus.CANCELLED)
            db.add(payment)
        db.commit()

    @classmethod
    def __get_timeout_payments(cls, db: Session):
        return (
            db.query(Payment)
            .filter(
                Payment.status.in_(
                    [
                        PaymentStatus.WAITING_FOR_PAYMENT_DETAIL,
                        PaymentStatus.WAITING_FOR_PURCHASE,
                        PaymentStatus.NEW,
                    ]
                ),
                Payment.deleted_at.is_(None),
                Payment.created_at < func.now() - timedelta(minutes=cls.PAYMENT_TIMEOUT_MINUTES),
            )
            .all()
        )
