from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.libs.database import with_db_session_for_class_instance
from app.models.order import Order
from app.models.store import Store


class GetOverviewOrderByDayBarChartOperation:
    
    def __init__(self, tenant_id: UUID):
        self.tenant_id = tenant_id
    
    @with_db_session_for_class_instance
    def execute(self, db: Session, start_date: datetime, end_date: datetime):
        date_expr = func.date(Order.created_at)
        filters = [Store.tenant_id == self.tenant_id]
        if start_date is not None:
            filters.append(date_expr >= start_date.date())
        if end_date is not None:
            filters.append(date_expr <= end_date.date())

        query = (
            db.query(Order)
            .join(Store, Order.store_id == Store.id)
            .filter(and_(*filters))
            .group_by(date_expr)
            .with_entities(
                date_expr.label("date"),
                func.count(Order.id).label("total_orders"),
            )
        )
        orders = query.all()

        orders_count_by_date = {row.date: int(row.total_orders) for row in orders}

        start_day = start_date.date()
        end_day = end_date.date()
        num_days = (end_day - start_day).days
        labels = []
        values = []
        for i in range(num_days + 1):
            current_day = start_day + timedelta(days=i)
            labels.append(current_day.strftime("%Y-%m-%d"))
            values.append(orders_count_by_date.get(current_day, 0))

        return {
            "labels": labels,
            "values": values,
        }
