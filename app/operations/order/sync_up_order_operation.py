from typing import List
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.libs.database import with_db_session_classmethod
from app.models import OrderDetail, PaymentStatus
from app.models.machine import Machine, MachineStatus
from app.models.order import Order, OrderDetailStatus, OrderStatus


class SyncUpOrderOperation:
    
    PAYMENT_TIMEOUT_MINUTES = 5
    
    @classmethod
    @with_db_session_classmethod
    def execute(cls, db: Session, order_id: uuid.UUID):
        logger.info(f"Syncing up order {order_id}")
        
        order = cls.__get_order(db, order_id)

        if order.status == OrderStatus.WAITING_FOR_PAYMENT:
            cls.__sync_up_waiting_for_payment(db, order)
        elif order.status == OrderStatus.IN_PROGRESS:
            cls.__sync_up_in_progress(db, order)
        else:
            logger.info(f"Order {order_id} is not in progress or waiting for payment")
            return

    @classmethod
    def __get_order(cls, db: Session, order_id: uuid.UUID):
        return db.query(Order).get(order_id)

    @classmethod
    def __sync_up_waiting_for_payment(cls, db: Session, order: Order):
        payments = order.payments
        if not payments:
            logger.info(f"No payments found for order {order.id}")
            return

        is_payment_failed = False
        for payment in payments:
            if payment.status in [PaymentStatus.FAILED, PaymentStatus.CANCELLED]:
                is_payment_failed = True
                break
        
        if not is_payment_failed:
            return

        order_details = (
            db.query(OrderDetail).filter(OrderDetail.order_id == order.id).all()
        )
        for order_detail in order_details:
            order_detail.status = OrderDetailStatus.CANCELLED
            db.add(order_detail)

        order.status = OrderStatus.PAYMENT_FAILED
        db.add(order)
        db.commit()
        return


    @classmethod
    def __sync_up_in_progress(cls, db: Session, order: Order):
        order_details = (
            db.query(OrderDetail).join(Machine, OrderDetail.machine_id == Machine.id)
            .filter(OrderDetail.order_id == order.id)
            .all()
        )

        for order_detail in order_details:
            logger.info(
                f"Syncing up order detail {order_detail.id} for order {order.id}",
                machine_status=order_detail.machine.status,
            )

            if order_detail.machine.status == MachineStatus.IDLE:
                order_detail.status = OrderDetailStatus.FINISHED
                db.add(order_detail)
        db.commit()

        if all(order_detail.status == OrderDetailStatus.FINISHED for order_detail in order.order_details):
            order.status = OrderStatus.FINISHED
            db.add(order)
            db.commit()
            return


