from uuid import UUID
from datetime import datetime
from typing import List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.libs.database import with_db_session_for_class_instance
from app.models.payment import PaymentStatus
from app.utils.timezone import get_tzinfo


class GetOverviewStoreKeyMetricsOperation:
    def __init__(self, tenant_id: UUID):
        self.tenant_id = tenant_id

    @with_db_session_for_class_instance
    def execute(self, db: Session) -> List[Dict[str, Any]]:
        store_key_metrics = self._list_store_key_metrics(db)
        return store_key_metrics

    def _list_store_key_metrics(self, db: Session) -> List[Dict[str, Any]]:
        start_date_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0).astimezone(get_tzinfo())
        end_date_of_month = datetime.now().replace(month=datetime.now().month + 1, day=1, hour=0, minute=0, second=0, microsecond=0).astimezone(get_tzinfo())
        
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
                AND orders.created_at >= :start_date
                AND orders.created_at < :end_date
                GROUP BY orders.store_id
            ) as key_metrics ON s.id = key_metrics.store_id
            WHERE s.tenant_id = :tenant_id
            AND s.deleted_at IS NULL
        """)
        
        result = db.execute(get_key_metrics_query, {
            "payment_status": PaymentStatus.SUCCESS,
            "tenant_id": self.tenant_id,
            "start_date": start_date_of_month.isoformat(),
            "end_date": end_date_of_month.isoformat(),
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
