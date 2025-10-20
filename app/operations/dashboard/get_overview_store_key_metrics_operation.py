from uuid import UUID
from datetime import date
from typing import List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, text

from app.libs.database import with_db_session_for_class_instance
from app.models.store import Store, StoreStatus
from app.models.order import Order, OrderStatus
from app.models.payment import Payment, PaymentStatus
from app.models.machine import Machine, MachineType, MachineStatus
from app.models.controller import Controller


class GetOverviewStoreKeyMetricsOperation:
    def __init__(self, tenant_id: UUID):
        self.tenant_id = tenant_id

    @with_db_session_for_class_instance
    def execute(self, db: Session) -> List[Dict[str, Any]]:
        store_key_metrics = self._list_store_key_metrics(db)
        return store_key_metrics

    def _list_store_key_metrics(self, db: Session) -> List[Dict[str, Any]]:
        """Get all active stores for the tenant with their key metrics"""
        get_key_metrics_query = text("""
            SELECT
                s.id,
                s.name,
                s.address,
                s.contact_phone_number,
                s.tenant_id,
                COALESCE(key_metrics.total_orders, 0) as total_orders,
                COALESCE(key_metrics.total_revenue, 0) as total_revenue
            FROM stores s
            LEFT JOIN (
                SELECT
                    orders.store_id,
                    COUNT(orders.id) as total_orders,
                    SUM(payments.total_amount) as total_revenue
                FROM orders
                JOIN payments ON orders.id = payments.order_id
                WHERE payments.status = :payment_status
                AND payments.deleted_at IS NULL
                AND orders.deleted_at IS NULL
                GROUP BY orders.store_id
            ) as key_metrics ON s.id = key_metrics.store_id
            WHERE s.tenant_id = :tenant_id
            AND s.deleted_at IS NULL
        """)
        
        result = db.execute(get_key_metrics_query, {
            "payment_status": PaymentStatus.SUCCESS,
            "tenant_id": self.tenant_id,
        }).fetchall()
        
        # Convert SQLAlchemy Row objects to dictionaries
        store_metrics = []
        for row in result:
            store_dict = {
                "id": str(row.id),
                "name": row.name,
                "address": row.address,
                "contact_phone_number": row.contact_phone_number,
                "tenant_id": str(row.tenant_id),
                "total_orders": row.total_orders,
                "total_revenue": float(row.total_revenue)
            }
            store_metrics.append(store_dict)
        
        return store_metrics
