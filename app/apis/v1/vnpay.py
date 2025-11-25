from fastapi import APIRouter, HTTPException
from app.core.logging import logger

from app.schemas.vnpay import VNPAYIpnRequest

from app.operations.payment.sync_up_vnpay_success_transaction_operation import (
    SyncUpVnPaySuccessTransactionOperation,
)
from app.operations.payment.sync_up_vnpay_failed_transaction_operation import (
    SyncUpVnPayFailedTransactionOperation,
)
from app.operations.payment.sync_up_vnpay_cancel_transaction_operation import (
    SyncUpVnPayCancelTransactionOperation,
)

router = APIRouter()


@router.post("/ipn")
def vnpay_ipn(request: VNPAYIpnRequest):
    """
    Unified VNPAY IPN handler
    Supports: Success (200), Failed (431), Cancel (434)
    """
    logger.info(f"[VNPAY IPN] Request received: {request}")

    try:
        response_code = request.responseCode

        if response_code == "200":
            logger.info("[VNPAY IPN] Status = SUCCESS (200)")
            op = SyncUpVnPaySuccessTransactionOperation(request)
            op.execute()
            return {"code": "200", "message": "Success"}

        elif response_code == "431":
            logger.info("[VNPAY IPN] Status = FAILED (431)")
            op = SyncUpVnPayFailedTransactionOperation(request)
            op.execute()
            return {"code": "200", "message": "Failed transaction updated"}

        elif response_code == "434":
            logger.info("[VNPAY IPN] Status = CANCELED (434)")
            op = SyncUpVnPayCancelTransactionOperation(request)
            op.execute()
            return {"code": "200", "message": "Cancelled transaction updated"}
        
        else:
            logger.error(f"[VNPAY IPN] Invalid responseCode: {response_code}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid response code: {response_code}"
            )

    except HTTPException as e:
        raise e

    except ValueError as e:
        logger.error(f"[VNPAY IPN] Business error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.exception("[VNPAY IPN] Unexpected server error")
        raise HTTPException(status_code=500, detail="Internal server error")

