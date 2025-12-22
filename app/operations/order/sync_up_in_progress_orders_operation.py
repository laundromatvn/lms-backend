from sqlalchemy.orm import Session

from app.core.logging import logger
from app.libs.database import with_db_session_classmethod
from app.models.order import Order, OrderStatus
from app.operations.order.sync_up_order_operation import SyncUpOrderOperation

class SyncUpInProgressOrdersOperation:
    
    @classmethod
    @with_db_session_classmethod
    def execute(cls, db: Session):
        orders = (
            db.query(Order)
            .filter(
                Order.status.in_([OrderStatus.IN_PROGRESS, OrderStatus.WAITING_FOR_PAYMENT]),
                Order.deleted_at.is_(None)
            )
            .order_by(Order.created_at.desc())
            .all()
        )
        if not orders:
            logger.info("No in progress orders found")
            return
        
        logger.info(f"Found {len(orders)} in progress orders")
        
        for order in orders:
            SyncUpOrderOperation.execute(order.id)
