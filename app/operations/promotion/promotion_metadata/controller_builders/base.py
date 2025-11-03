from abc import ABC, abstractmethod
from typing import List, Any

from app.enums.promotion.condition_type import ConditionType


class BasePromotionConditionBuilder(ABC):
    condition_type: ConditionType

    def __init__(self, current_user):
        self.current_user = current_user

    @abstractmethod
    def build_options(self) -> List[Any]:
        pass


