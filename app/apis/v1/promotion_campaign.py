from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.apis.deps import get_current_user
from app.core.logging import logger
from app.models.user import User
from app.operations.promotion.promotion_base_service import PromotionBaseService
from app.operations.promotion.promotion_metadata.build_promotion_metadata_operation import BuildPromotionMetadataOperation
from app.schemas.pagination import PaginatedResponse
from app.schemas.promotion.promotion import (
    PromotionCampaignSerializer,
    ListPromotionCampaignQueryParams,
    PromotionCampaignCreate,
    PromotionCampaignUpdate,
)
from app.schemas.promotion.promotion import PromotionMetadata
from app.utils.pagination import get_total_pages

router = APIRouter()


@router.get("/metadata", response_model=PromotionMetadata)
async def get_promotion_metadata(
    current_user: User = Depends(get_current_user),
):
    try:
        return await BuildPromotionMetadataOperation(current_user).execute()
    except Exception as e:
        logger.error("Get promotion metadata failed", type=type(e).__name__, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=PaginatedResponse[PromotionCampaignSerializer])
async def list_promotion_campaigns(
    query_params: ListPromotionCampaignQueryParams = Depends(),
    current_user: User = Depends(get_current_user),
):
    try:
        total, promotion_campaigns = PromotionBaseService.list(current_user, query_params)
        
        return {
            "page": query_params.page,
            "page_size": query_params.page_size,
            "total": total,
            "total_pages": get_total_pages(total, query_params.page_size),
            "data": promotion_campaigns,
        }
    except Exception as e:
        logger.error("List promotion campaigns failed", type=type(e).__name__, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=PromotionCampaignSerializer)
async def create_promotion_campaign(
    request: PromotionCampaignCreate,
    current_user: User = Depends(get_current_user),
):
    try:
        return PromotionBaseService.create(current_user, request)
    except Exception as e:
        logger.error("Create promotion campaign failed", type=type(e).__name__, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{promotion_campaign_id}", response_model=PromotionCampaignSerializer)
async def get_promotion_campaign(
    promotion_campaign_id: UUID,
    current_user: User = Depends(get_current_user),
):
    try:
        promotion_campaign = PromotionBaseService.get(current_user, promotion_campaign_id)
        return promotion_campaign
    except Exception as e:
        logger.error("Get promotion campaign failed", type=type(e).__name__, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
    
    
@router.patch("/{promotion_campaign_id}", response_model=PromotionCampaignSerializer)
async def update_partially_promotion_campaign(
    promotion_campaign_id: UUID,
    request: PromotionCampaignUpdate,
    current_user: User = Depends(get_current_user),
):
    try:
        return PromotionBaseService.update_partially(current_user, promotion_campaign_id, request)
    except Exception as e:
        logger.error("Update promotion campaign failed", type=type(e).__name__, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
