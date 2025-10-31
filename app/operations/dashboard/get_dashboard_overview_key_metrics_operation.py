from uuid import UUID
from datetime import date

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.core.logging import logger
from app.core.config import settings
from app.libs.database import with_db_session_for_class_instance
from app.models.machine import Machine, MachineType, MachineStatus
from app.models.store import Store, StoreStatus
from app.models.order import Order, OrderStatus
from app.models.payment import Payment, PaymentStatus
from app.models.controller import Controller


class GetDashboardOverviewKeyMetricsOperation:
    
    def __init__(self, tenant_id: UUID):
        self.tenant_id = tenant_id
    
    @with_db_session_for_class_instance
    def execute(self, db: Session):
        total_stores, total_active_stores = self._get_stores_key_metrics(db)
        
        total_washers, total_in_progress_washers = self._get_washers_key_metrics(db)
        
        total_dryers, total_in_progress_dryers = self._get_dryers_key_metrics(db)
        
        today_orders, total_in_progress_orders = self._get_orders_key_metrics(db)
        
        revenue_by_day, revenue_by_month = self._get_revenue_key_metrics(db)
        
        return {    
            "total_active_stores": total_active_stores,
            "total_stores": total_stores,
            "total_in_progress_washers": total_in_progress_washers,
            "total_washers": total_washers,
            "total_in_progress_dryers": total_in_progress_dryers,
            "total_dryers": total_dryers,
            "total_in_progress_orders": total_in_progress_orders,
            "today_orders": today_orders,
            "revenue_by_day": revenue_by_day,
            "revenue_by_month": revenue_by_month,
        }

    def _get_stores_key_metrics(self, db: Session):
        """Get total stores and active stores count for the tenant"""
        # Get total stores (excluding soft deleted)
        total_stores = (
            db.query(Store)
            .filter(
                and_(
                    Store.tenant_id == self.tenant_id,
                    Store.deleted_at.is_(None)
                )
            )
            .count()
        )
        
        # Get active stores (status = ACTIVE and not deleted)
        total_active_stores = (
            db.query(Store)
            .filter(
                and_(
                    Store.tenant_id == self.tenant_id,
                    Store.status == StoreStatus.ACTIVE,
                    Store.deleted_at.is_(None)
                )
            )
            .count()
        )
        
        return total_stores, total_active_stores

    def _get_washers_key_metrics(self, db: Session):
        """Get total washers and in-progress washers count for the tenant"""
        # Get total washers (excluding soft deleted)
        total_washers = (
            db.query(Machine)
            .join(Controller)
            .join(Store)
            .filter(
                and_(
                    Store.tenant_id == self.tenant_id,
                    Machine.machine_type == MachineType.WASHER,
                    Machine.deleted_at.is_(None)
                )
            )
            .count()
        )
        
        # Get in-progress washers (status = BUSY or STARTING)
        total_in_progress_washers = (
            db.query(Machine)
            .join(Controller)
            .join(Store)
            .filter(
                and_(
                    Store.tenant_id == self.tenant_id,
                    Machine.machine_type == MachineType.WASHER,
                    Machine.status.in_([MachineStatus.BUSY, MachineStatus.STARTING]),
                    Machine.deleted_at.is_(None)
                )
            )
            .count()
        )
        
        return total_washers, total_in_progress_washers
    
    def _get_dryers_key_metrics(self, db: Session):
        """Get total dryers and in-progress dryers count for the tenant"""
        # Get total dryers (excluding soft deleted)
        total_dryers = (
            db.query(Machine)
            .join(Controller)
            .join(Store)
            .filter(
                and_(
                    Store.tenant_id == self.tenant_id,
                    Machine.machine_type == MachineType.DRYER,
                    Machine.deleted_at.is_(None)
                )
            )
            .count()
        )
        
        # Get in-progress dryers (status = BUSY or STARTING)
        total_in_progress_dryers = (
            db.query(Machine)
            .join(Controller)
            .join(Store)
            .filter(
                and_(
                    Store.tenant_id == self.tenant_id,
                    Machine.machine_type == MachineType.DRYER,
                    Machine.status.in_([MachineStatus.BUSY, MachineStatus.STARTING]),
                    Machine.deleted_at.is_(None)
                )
            )
            .count()
        )
        
        return total_dryers, total_in_progress_dryers
    
    def _get_orders_key_metrics(self, db: Session):
        """Get today's orders and in-progress orders count for the tenant"""
        today = date.today()
        
        # Get today's orders (excluding soft deleted)
        # Use timezone conversion to ensure consistent date extraction
        today_orders = (
            db.query(Order)
            .join(Store)
            .filter(
                and_(
                    Store.tenant_id == self.tenant_id,
                    func.date(
                        func.timezone(settings.TIMEZONE_NAME, Order.created_at)
                    ) == today,
                    Order.deleted_at.is_(None)
                )
            )
            .count()
        )
        
        # Get in-progress orders (status = IN_PROGRESS)
        total_in_progress_orders = (
            db.query(Order)
            .join(Store)
            .filter(
                and_(
                    Store.tenant_id == self.tenant_id,
                    Order.status == OrderStatus.IN_PROGRESS,
                    func.date(
                        func.timezone(settings.TIMEZONE_NAME, Order.created_at)
                    ) == today,
                    Order.deleted_at.is_(None)
                )
            )
            .count()
        )
        
        return today_orders, total_in_progress_orders
    
    def _get_revenue_key_metrics(self, db: Session):
        """Get revenue by day (today) and by month (current month) from successful payments for the tenant"""
        today = date.today()
        current_month = today.month
        current_year = today.year
        
        # Get today's revenue from successful payments
        # Use timezone conversion to ensure consistent date extraction
        # Convert Payment.created_at to application timezone before extracting date
        revenue_by_day = (
            db.query(func.coalesce(func.sum(Payment.total_amount), 0))
            .join(Store)
            .filter(
                and_(
                    Store.tenant_id == self.tenant_id,
                    Payment.status == PaymentStatus.SUCCESS,
                    func.date(
                        func.timezone(settings.TIMEZONE_NAME, Payment.created_at)
                    ) == today,
                    Payment.deleted_at.is_(None)
                )
            )
            .scalar()
        )
        
        # trigger load
        logger.info(f"revenue_by_day: {revenue_by_day}")
        
        # Get current month's revenue from successful payments
        # Use timezone conversion for month extraction as well
        revenue_by_month = (
            db.query(func.coalesce(func.sum(Payment.total_amount), 0))
            .join(Store)
            .filter(
                and_(
                    Store.tenant_id == self.tenant_id,
                    Payment.status == PaymentStatus.SUCCESS,
                    func.extract(
                        'year',
                        func.timezone(settings.TIMEZONE_NAME, Payment.created_at)
                    ) == current_year,
                    func.extract(
                        'month',
                        func.timezone(settings.TIMEZONE_NAME, Payment.created_at)
                    ) == current_month,
                    Payment.deleted_at.is_(None)
                )
            )
            .scalar()
        )
        
        
        # trigger load
        logger.info(f"revenue_by_month: {revenue_by_month}")

        # Convert to float for JSON serialization
        return (
            float(revenue_by_day) if revenue_by_day else 0.0,
            float(revenue_by_month) if revenue_by_month else 0.0
        )
