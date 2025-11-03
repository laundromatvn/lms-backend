from typing import List, Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.enums.promotion.condition_type import ConditionType
from app.libs.database import with_db_session_for_class_instance
from app.models.tenant_member import TenantMember
from app.models.store import Store

from .base import BasePromotionConditionBuilder
from .registry import PromotionConditionBuilderRegistry


CONDITION_TYPE = ConditionType.STORES


@PromotionConditionBuilderRegistry.register(CONDITION_TYPE)
class StorePromotionConditionBuilder(BasePromotionConditionBuilder):
    condition_type = CONDITION_TYPE

    @with_db_session_for_class_instance
    def build_options(self, db: Session) -> List[Any]:
        if self.current_user.is_admin:
            return self._get_admin_store_ids(db)
        else:
            return self._get_tenant_store_ids(db)

    def _get_admin_store_ids(self, db: Session) -> List[UUID]:
        stores = (
            db.query(Store)
            .filter(Store.deleted_at.is_(None))
            .all()
        )

        return [store.id for store in stores]

    def _get_tenant_store_ids(self, db: Session) -> List[UUID]:
        current_user_tenant_members = (
            db.query(TenantMember.tenant_id)
            .filter(TenantMember.user_id == self.current_user.id)
            .filter(TenantMember.is_enabled == True)
            .distinct()
            .all()
        )
        tenant_ids = [tenant.tenant_id for tenant in current_user_tenant_members]

        stores = (
            db.query(Store)
            .filter(Store.deleted_at.is_(None))
            .filter(Store.tenant_id.in_(tenant_ids))
            .all()
        )

        return [store.id for store in stores]
