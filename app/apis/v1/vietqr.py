from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBasicCredentials

from app.apis.deps import verify_vietqr_partner_credentials, get_vietqr_internal_user
from app.models.payment import PaymentStatus
from app.models.user import User
from app.core.config import settings
from app.core.logging import logger
from app.schemas.vietqr import VietQRTokenGenerateResponse, VietQRTransactionSyncRequest, VietQRTransactionSyncResponse
from app.utils.security.jwt import create_access_token
from app.tasks.payment.payment_tasks import sync_payment_transaction


router = APIRouter()


@router.post("/api/token_generate", response_model=VietQRTokenGenerateResponse)
async def generate_vietqr_token(
    credentials: HTTPBasicCredentials = Depends(verify_vietqr_partner_credentials),
):
    """
    Generate access token for VietQR partner to access LMS system.
    
    This endpoint allows VietQR to obtain a Bearer token for authenticating
    with the LMS system for transaction synchronization.
    
    Authentication: Basic Auth with VietQR partner credentials
    """
    try:
        token_data = {
            "vietqr_partner": True,
            "username": credentials.username,
            "purpose": "transaction_sync"
        }

        expires_delta = timedelta(seconds=settings.VIETQR_TOKEN_EXPIRE_SECONDS)
        access_token = create_access_token(
            data=token_data,
            expires_delta=expires_delta
        )
        
        logger.info(f"Generated VietQR token for partner: {credentials.username}")
        
        return VietQRTokenGenerateResponse(
            access_token=access_token,
            token_type="Bearer",
            expires_in=settings.VIETQR_TOKEN_EXPIRE_SECONDS
        )
        
    except Exception as e:
        logger.error(f"Error generating VietQR token: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while generating token"
        )


@router.post("/api/transaction-sync", response_model=VietQRTransactionSyncResponse)
async def transaction_sync(
    request: VietQRTransactionSyncRequest,
    _: User = Depends(get_vietqr_internal_user),
):
    """
    Synchronize transaction with VietQR.
    
    This endpoint receives transaction data from VietQR and processes it
    in the LMS system. It validates the transaction and returns a response
    indicating success or failure.
    
    Authentication: Bearer token from VietQR partner
    """
    try:
        # Log the incoming transaction for debugging
        logger.info(f"Received transaction sync request: {request.transactionid} for order: {request.orderId}")
        
        # Log transaction details as json
        logger.info(f"Transaction details: {request.model_dump_json()}")

        # Validate transaction type
        if request.transType not in ["D", "C"]:
            return VietQRTransactionSyncResponse(
                error=True,
                errorReason="INVALID_TRANS_TYPE",
                toastMessage="Transaction type must be 'D' (debit) or 'C' (credit)",
                object=None
            )

        # Validate amount
        if float(request.amount) <= 0:
            return VietQRTransactionSyncResponse(
                error=True,
                errorReason="INVALID_AMOUNT",
                toastMessage="Transaction amount must be greater than 0",
                object=None
            )

        sync_payment_transaction(
            content=request.content,
            status=PaymentStatus.SUCCESS,
            provider="VIET_QR"
        )

        return VietQRTransactionSyncResponse(
            error=False,
            errorReason="",
            toastMessage="Transaction synchronized successfully",
            object={
                "reftransactionid": request.transactionid
            }
        )

    except Exception as e:
        logger.error(f"Error synchronizing transaction with VietQR: {str(e)}")
        return VietQRTransactionSyncResponse(
            error=True,
            errorReason="INTERNAL_ERROR",
            toastMessage="Internal server error while processing transaction",
            object=None
        )
