from decimal import Decimal
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.apis.deps import require_permissions
from app.libs.database import get_db
from app.models.user import User
from app.operations.subscription.list_subscription_plans import ListSubscriptionPlansOperation
from app.operations.subscription.add_subscription_plan import AddSubscriptionPlanOperation
from app.schemas.subscription import (
    SubscriptionPlanSerializer,
    SubscriptionPlanCreatePayload,
    ListSubscriptionPlansQueryParams,
)
from app.schemas.pagination import PaginatedResponse
from app.utils.pagination import get_total_pages

router = APIRouter()
    

@router.get("", response_model=PaginatedResponse[SubscriptionPlanSerializer])
def list_subscription_plans(
    query_params: ListSubscriptionPlansQueryParams = Depends(),
    current_user: User = Depends(require_permissions(["subscription_plan.list"])),
    db: Session = Depends(get_db),
):
    try:
        operation = ListSubscriptionPlansOperation(db, current_user, query_params)
        total, subscription_plans = operation.execute()
        return PaginatedResponse(
            page=query_params.page,
            page_size=query_params.page_size,
            total=total,
            total_pages=get_total_pages(total, query_params.page_size),
            data=subscription_plans,
        )
    except PermissionError:
        raise HTTPException(status_code=403)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("", status_code=201)
def create_subscription_plan(
    payload: SubscriptionPlanCreatePayload,
    current_user: User = Depends(require_permissions(["subscription_plan.create"])),
    db: Session = Depends(get_db),
):
    try:
        operation = AddSubscriptionPlanOperation(db, current_user, payload)
        operation.execute()
    except PermissionError:
        raise HTTPException(status_code=403)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))
