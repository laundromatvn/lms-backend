from app.enums.promotion.condition_type import ConditionType


class PromotionConditionBuilderRegistry:
    _builders = {}

    @classmethod
    def register(cls, condition_type: ConditionType):
        def decorator(builder_cls):
            cls._builders[condition_type] = builder_cls
            return builder_cls
        return decorator

    @classmethod
    def get_builder(cls, condition_type: ConditionType):
        return cls._builders.get(condition_type)


