from fastapi import APIRouter, HTTPException

from app.core.logging import logger
from app.operations.payment.sync_up_vnpay_success_transaction_operation import SyncUpVnPaySuccessTransactionOperation
from app.operations.payment.sync_up_vnpay_cancel_transaction_operation import SyncUpVnPayCancelTransactionOperation
from app.schemas.vnpay import (
    VNPAYSyncUpSuccessTransactionRequest,
    VNPAYSyncUpCancelTransactionRequest
)


router = APIRouter()


@router.post("/success")
def sync_up_success_transaction(request: VNPAYSyncUpSuccessTransactionRequest):
    try:
        logger.info(f"Syncing up success transaction: {request}")
        operation = SyncUpVnPaySuccessTransactionOperation(request)
        operation.execute()
        return {
            "code": "200",
            "message": "Success"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/cancel")
def sync_up_cancel_transaction(request: VNPAYSyncUpCancelTransactionRequest):
    try:
        logger.info(f"Syncing up cancel transaction: {request}")
        operation = SyncUpVnPayCancelTransactionOperation(request)
        operation.execute()
        return {
            "code": "200",
            "message": "Success"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


