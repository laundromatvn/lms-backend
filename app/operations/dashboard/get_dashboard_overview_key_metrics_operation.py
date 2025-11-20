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
    
    def __init__(self, tenant_id: UUID | None = None, store_id: UUID | None = None):
        self.tenant_id = tenant_id
        self.store_id = store_id

    @with_db_session_for_class_instance
    def execute(self, db: Session):
        total_stores = self._get_total_stores(db)
        total_active_stores = self._get_active_stores(db)
        
        total_washers = self._get_total_washers(db)
        total_in_progress_washers = self._get_in_progress_washers(db)
        
        total_dryers = self._get_total_dryers(db)
        total_in_progress_dryers = self._get_in_progress_dryers(db)
        
        today_orders = self._get_today_orders(db)
        total_in_progress_orders = self._get_in_progress_orders(db)
        
        revenue_by_day = self._get_today_revenue(db)
        revenue_by_month = self._get_current_month_revenue(db)

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
        
    def _get_total_stores(self, db: Session):
        base_query = (
            db.query(Store)
            .filter(Store.deleted_at.is_(None))
        )

        if self.tenant_id:
            base_query = base_query.filter(Store.tenant_id == self.tenant_id)
        
        if self.store_id:
            base_query = base_query.filter(Store.id == self.store_id)
        
        return base_query.count()
    
    def _get_active_stores(self, db: Session):
        base_query = (
            db.query(Store)
            .filter(Store.deleted_at.is_(None))
            .filter(Store.status == StoreStatus.ACTIVE)
        )
        
        if self.tenant_id:
            base_query = base_query.filter(Store.tenant_id == self.tenant_id)

        if self.store_id:
            base_query = base_query.filter(Store.id == self.store_id)
        
        return base_query.count()

    def _get_total_washers(self, db: Session):
        base_query = (
            db.query(Machine)
            .join(Controller)
            .join(Store)
            .filter(Machine.machine_type == MachineType.WASHER)
            .filter(Machine.deleted_at.is_(None))
        )
        
        if self.tenant_id:
            base_query = base_query.filter(Store.tenant_id == self.tenant_id)
        
        if self.store_id:
            base_query = base_query.filter(Store.id == self.store_id)
        
        return base_query.count()
    
    def _get_in_progress_washers(self, db: Session):
        base_query = (
            db.query(Machine)
            .join(Controller)
            .join(Store)
            .filter(Machine.machine_type == MachineType.WASHER)
            .filter(Machine.status.in_([MachineStatus.BUSY, MachineStatus.STARTING]))
            .filter(Machine.deleted_at.is_(None))
        )
        
        if self.tenant_id:
            base_query = base_query.filter(Store.tenant_id == self.tenant_id)
        
        if self.store_id:
            base_query = base_query.filter(Store.id == self.store_id)
        
        return base_query.count()

    def _get_total_dryers(self, db: Session):
        base_query = (
            db.query(Machine)
            .join(Controller)
            .join(Store)
            .filter(Machine.machine_type == MachineType.DRYER)
            .filter(Machine.deleted_at.is_(None))
        )
        
        if self.tenant_id:
            base_query = base_query.filter(Store.tenant_id == self.tenant_id)
        
        if self.store_id:
            base_query = base_query.filter(Store.id == self.store_id)
        
        return base_query.count()

    def _get_in_progress_dryers(self, db: Session):
        base_query = (
            db.query(Machine)
            .join(Controller)
            .join(Store)
            .filter(Machine.machine_type == MachineType.DRYER)
            .filter(Machine.status.in_([MachineStatus.BUSY, MachineStatus.STARTING]))
            .filter(Machine.deleted_at.is_(None))
        )
        
        if self.tenant_id:
            base_query = base_query.filter(Store.tenant_id == self.tenant_id)
        
        if self.store_id:
            base_query = base_query.filter(Store.id == self.store_id)
        
        return base_query.count()

    def _get_today_orders(self, db: Session):
        base_query = (
            db.query(Order)
            .join(Store)
            .filter(func.date(func.timezone(settings.TIMEZONE_NAME, Order.created_at)) == date.today())
            .filter(Order.deleted_at.is_(None))
        )

        if self.store_id:
            base_query = base_query.filter(Store.id == self.store_id)

        if self.tenant_id:
            base_query = base_query.filter(Store.tenant_id == self.tenant_id)

        return base_query.count()
    
    def _get_in_progress_orders(self, db: Session):
        base_query = (
            db.query(Order)
            .join(Store)
            .filter(Order.status == OrderStatus.IN_PROGRESS)
            .filter(Order.deleted_at.is_(None))
        )
        
        if self.store_id:
            base_query = base_query.filter(Store.id == self.store_id)

        if self.tenant_id:
            base_query = base_query.filter(Store.tenant_id == self.tenant_id)

        return base_query.count()

    def _get_today_revenue(self, db: Session):
        base_query = (
            db.query(func.coalesce(func.sum(Payment.total_amount), 0))
            .join(Store)
            .filter(Payment.status == PaymentStatus.SUCCESS)
            .filter(Payment.deleted_at.is_(None))
            .filter(func.date(func.timezone(settings.TIMEZONE_NAME, Payment.created_at)) == date.today())
        )
        
        if self.store_id:
            base_query = base_query.filter(Store.id == self.store_id)
    
        if self.tenant_id:
            base_query = base_query.filter(Store.tenant_id == self.tenant_id)
    
        return base_query.scalar()
    
    def _get_current_month_revenue(self, db: Session):
        base_query = (
            db.query(func.coalesce(func.sum(Payment.total_amount), 0))
            .join(Store)
            .filter(Payment.status == PaymentStatus.SUCCESS)
            .filter(Payment.deleted_at.is_(None))
            .filter(func.extract('year', func.timezone(settings.TIMEZONE_NAME, Payment.created_at)) == date.today().year)
            .filter(func.extract('month', func.timezone(settings.TIMEZONE_NAME, Payment.created_at)) == date.today().month)
        )

        if self.store_id:
            base_query = base_query.filter(Store.id == self.store_id)

        if self.tenant_id:
            base_query = base_query.filter(Store.tenant_id == self.tenant_id)

        return base_query.scalar()
