from typing import List
import uuid

from sqlalchemy.orm import Session

from app.core.logging import logger
from app.libs.database import with_db_session_classmethod
from app.models import OrderDetail
from app.models.machine import Machine, MachineStatus
from app.models.order import Order, OrderDetailStatus, OrderStatus


class SyncUpOrderOperation:
    
    @classmethod
    @with_db_session_classmethod
    def execute(cls, db: Session, order_id: uuid.UUID):
        logger.info(f"Syncing up order {order_id}")
        
        cls.__sync_up_order_details(db, order_id)

        cls.__sync_up_order(db, order_id)

    @classmethod
    def __sync_up_order_details(cls, db: Session, order_id: uuid.UUID):
        order_details = (
            db.query(OrderDetail).join(Machine, OrderDetail.machine_id == Machine.id)
            .filter(OrderDetail.order_id == order_id)
            .all()
        )

        for order_detail in order_details:
            logger.info(
                f"Syncing up order detail {order_detail.id} for order {order_id}",
                machine_status=order_detail.machine.status,
            )
            if order_detail.machine.status == MachineStatus.IDLE:
                order_detail.status = OrderDetailStatus.FINISHED
                db.add(order_detail)

        db.commit()

    @classmethod
    def __sync_up_order(cls, db: Session, order_id: uuid.UUID):
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            logger.info(f"Order with ID {order_id} not found")
            return

        if all(order_detail.status == OrderDetailStatus.FINISHED for order_detail in order.order_details):
            order.status = OrderStatus.FINISHED
            db.add(order)
            db.commit()
            return
