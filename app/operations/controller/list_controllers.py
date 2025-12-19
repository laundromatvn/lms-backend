from typing import List
from sqlalchemy.orm import Session, Query

from app.models.controller import Controller, ControllerStatus
from app.models.firmware import Firmware
from app.models.order import Order
from app.models.store import Store
from app.models.store_member import StoreMember
from app.models.tenant_member import TenantMember
from app.models.user import User
from app.schemas.controller import ListControllerQueryParams


class ListControllersOperation:

    def __init__(
        self, 
        db: Session, 
        current_user: User, 
        query_params: ListControllerQueryParams,
    ):
        self.db = db
        self.current_user = current_user
        self.query_params = query_params

    def execute(self) -> tuple[int, List[Order]]:
        base_query = self._build_base_query()

        base_query = self._apply_filters(base_query)
        base_query = self._apply_ordering(base_query)

        total = base_query.count()
        stores = (
            base_query.offset(
                (self.query_params.page - 1) * self.query_params.page_size
            )
            .limit(self.query_params.page_size)
            .all()
        )
        
        return total, stores

    def _build_base_query(self) -> Query:
        base_query = (
            self.db.query(
                *Controller.__table__.columns,
                Store.id.label('store_id'),
                Store.name.label('store_name'),
                Firmware.id.label('firmware_id'),
                Firmware.name.label('firmware_name'),
                Firmware.version.label('firmware_version'),
            )
            .outerjoin(Store, Controller.store_id == Store.id)
            .outerjoin(Firmware, Controller.provisioned_firmware_id == Firmware.id)
            .filter(
                Controller.deleted_at.is_(None),
                Controller.status.notin_([ControllerStatus.INACTIVE]),
            )
        )
        
        if self.current_user.is_tenant_admin:
            store_ids_sub_query = (
                self.db.query(Store.id)
                .join(TenantMember, Store.tenant_id == TenantMember.tenant_id)
                .filter(
                    TenantMember.user_id == self.current_user.id,
                )
                .subquery()
            )
            
            base_query = base_query.filter(Controller.store_id.in_(store_ids_sub_query))

        elif self.current_user.is_tenant_staff:
            store_ids_sub_query = (
                self.db.query(Store.id)
                .join(StoreMember, Store.id == StoreMember.store_id)
                .filter(StoreMember.user_id == self.current_user.id)
                .subquery()
            )
            
            base_query = base_query.filter(Controller.store_id.in_(store_ids_sub_query))

        return base_query

    def _apply_filters(self, base_query: Query) -> Query:
        if self.query_params.status:
            base_query = base_query.filter(Controller.status == self.query_params.status)

        if self.query_params.store_id:
            base_query = base_query.filter(Controller.store_id == self.query_params.store_id)
            
        if self.query_params.store_name:
            base_query = base_query.filter(Store.name.ilike(f"%{self.query_params.store_name}%"))

        return base_query

    def _apply_ordering(self, base_query: Query) -> Query:
        if not self.query_params.order_by: return base_query
        
        if self.query_params.order_by == "store_name":
            if self.query_params.order_direction == "desc":
                base_query = base_query.order_by(Store.name.desc())
            else:
                base_query = base_query.order_by(Store.name.asc())
        elif self.query_params.order_by:
            if self.query_params.order_direction == "desc":
                base_query = base_query.order_by(getattr(Controller, self.query_params.order_by).desc())
            else:
                base_query = base_query.order_by(getattr(Controller, self.query_params.order_by).asc())
        else:
            base_query = base_query.order_by(Controller.created_at.desc())
            
        return base_query
