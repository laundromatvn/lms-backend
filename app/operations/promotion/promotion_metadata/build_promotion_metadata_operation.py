from typing import List

from app.models.user import User, UserRole
from app.schemas.promotion.promotion import PromotionMetadata
from app.schemas.promotion.metadata import (
    CONDITION_METADATA, REWARD_METADATA, LIMIT_METADATA,
    ConditionMetadata, RewardMetadata, LimitMetadata
)

from .controller_builders.registry import PromotionConditionBuilderRegistry


class BuildPromotionMetadataOperation:
    def __init__(self, current_user: User):
        self.current_user = current_user

    async def execute(self) -> PromotionMetadata:
        return PromotionMetadata(
            conditions= await self._build_conditions(),
            rewards= await self._build_rewards(),
            limits= await self._build_limits(),
        )

    async def _build_conditions(self) -> List[ConditionMetadata]:
        conditions = []

        for meta in CONDITION_METADATA:
            if not self._has_permission(self.current_user.role, meta.allowed_roles):
                continue

            registered_builder = PromotionConditionBuilderRegistry.get_builder(meta.condition_type)

            if registered_builder:
                builder = registered_builder(self.current_user)
                meta.options = builder.build_options()
            else:
                meta.options = None

            conditions.append(meta)

        return conditions

    async def _build_rewards(self) -> List[RewardMetadata]:
        return REWARD_METADATA

    async def _build_limits(self) -> List[LimitMetadata]:
        return LIMIT_METADATA

    def _has_permission(
        self,
        current_user_role: UserRole,
        allowed_roles: List[UserRole] | None = None,
    ) -> bool:
        
        if not allowed_roles:
            raise ValueError("allowed_roles is required")

        return current_user_role in allowed_roles


