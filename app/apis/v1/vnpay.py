from fastapi import APIRouter, HTTPException

from app.core.logging import logger
from app.operations.payment.sync_up_vnpay_success_transaction_operation import SyncUpVnPaySuccessTransactionOperation
from app.operations.payment.sync_up_vnpay_cancel_transaction_operation import SyncUpVnPayCancelTransactionOperation
from app.schemas.vnpay import VNPAYIpnRequest


router = APIRouter()


@router.post("/ipn")
def vnpay_ipn(request: VNPAYIpnRequest):
    """
    VNPAY IPN endpoint.

    This endpoint receives IPN requests from VNPAY and processes them.
    It validates the request and updates the payment status accordingly.
    """
    try:
        logger.info(f"VNPAY IPN request: {request}")

        if request.responseCode == "200":
            operation = SyncUpVnPaySuccessTransactionOperation(request)
            operation.execute()
        elif request.responseCode == "434":
            operation = SyncUpVnPayCancelTransactionOperation(request)
            operation.execute()
        else:
            raise ValueError(f"Invalid response code: {request.responseCode}")

        return {"code": "200", "message": "Success"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


