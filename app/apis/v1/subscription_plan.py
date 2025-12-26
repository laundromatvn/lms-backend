from decimal import Decimal
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.apis.deps import require_permissions
from app.libs.database import get_db
from app.models.user import User
from app.operations.subscription.delete_subscription_plan import DeleteSubscriptionPlanOperation
from app.operations.subscription.get_subscription_plan import GetSubscriptionPlanOperation
from app.operations.subscription.list_subscription_plans import ListSubscriptionPlansOperation
from app.operations.subscription.add_subscription_plan import AddSubscriptionPlanOperation
from app.operations.subscription.update_subscription_plan import UpdateSubscriptionPlanOperation
from app.operations.subscription.list_subscription_plan_permissions import ListSubscriptionPlansPermissionsOperation
from app.schemas.subscription import (
    SubscriptionPlanSerializer,
    SubscriptionPlanCreatePayload,
    ListSubscriptionPlansQueryParams,
    SubscriptionPlanUpdatePayload,
    ListSubscriptionPlansPermissionsQueryParams,
)
from app.schemas.permission import PermissionSerializer
from app.schemas.pagination import PaginatedResponse
from app.utils.pagination import get_total_pages

router = APIRouter()


@router.get("/{subscription_plan_id}/permissions", response_model=PaginatedResponse[PermissionSerializer])
def get_subscription_plan_permissions(
    subscription_plan_id: UUID,
    query_params: ListSubscriptionPlansPermissionsQueryParams = Depends(),
    current_user: User = Depends(require_permissions(["subscription_plan.get"])),
    db: Session = Depends(get_db),
):
    try:
        operation = ListSubscriptionPlansPermissionsOperation(
            db,
            current_user,
            subscription_plan_id,
            query_params,
        )
        total, permissions = operation.execute()
        return PaginatedResponse(
            page=query_params.page,
            page_size=query_params.page_size,
            total=total,
            total_pages=get_total_pages(total, query_params.page_size),
            data=permissions,
        )
    except PermissionError:
        raise HTTPException(status_code=403)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/{subscription_plan_id}", response_model=SubscriptionPlanSerializer)
def get_subscription_plan(
    subscription_plan_id: UUID,
    current_user: User = Depends(require_permissions(["subscription_plan.get"])),
    db: Session = Depends(get_db),
):
    try:
        operation = GetSubscriptionPlanOperation(db, current_user, subscription_plan_id)
        return operation.execute()
    except PermissionError:
        raise HTTPException(status_code=403)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))
    
    
@router.patch("/{subscription_plan_id}", status_code=204)
def update_subscription_plan(
    subscription_plan_id: UUID,
    payload: SubscriptionPlanUpdatePayload,
    current_user: User = Depends(require_permissions(["subscription_plan.update"])),
    db: Session = Depends(get_db),
):
    try:
        operation = UpdateSubscriptionPlanOperation(db, current_user, subscription_plan_id, payload)
        operation.execute()
    except PermissionError:
        raise HTTPException(status_code=403)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.delete("/{subscription_plan_id}", status_code=204)
def delete_subscription_plan(
    subscription_plan_id: UUID,
    current_user: User = Depends(require_permissions(["subscription_plan.delete"])),
    db: Session = Depends(get_db),
):
    try:
        operation = DeleteSubscriptionPlanOperation(db, current_user, subscription_plan_id)
        operation.execute()
    except PermissionError:
        raise HTTPException(status_code=403)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


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
