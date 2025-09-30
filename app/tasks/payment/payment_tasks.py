import uuid
from app.core.celery_app import celery_app
from app.core.logging import logger
from app.operations.payment.payment_operation import PaymentOperation


@celery_app.task(name="app.tasks.payment.generate_payment_details")
def generate_payment_details(payment_id: str):
    """
    Generate payment details including QR code asynchronously.
    
    Args:
        payment_id: Payment transaction ID as string
        
    Returns:
        Dict containing task result and payment details
    """
    payment_id = uuid.UUID(payment_id)
    
    try:
        logger.info(f"Starting payment details generation for payment {payment_id}")
        
        # Generate payment details using the operation
        payment = PaymentOperation.generate_payment_details(payment_id)
        
        logger.info(
            f"Payment details generated successfully for payment {payment_id}",
            status=payment.status.value,
            transaction_id=payment.provider_transaction_id
        )
        
        return {
            "success": True,
            "payment_id": payment_id,
            "status": payment.status.value,
            "transaction_id": payment.provider_transaction_id,
            "qr_code": payment.details.get("qr_code") if payment.details else None,
            "expires_at": payment.details.get("expires_at") if payment.details else None,
            "message": "Payment details generated successfully"
        }
        
    except ValueError as e:
        logger.error(f"Payment details generation failed - validation error: {str(e)}", payment_id=payment_id)
        return {
            "success": False,
            "payment_id": payment_id,
            "error": "validation_error",
            "message": str(e)
        }
        
    except Exception as e:
        logger.error(
            f"Payment details generation failed - unexpected error: {str(e)}",
            payment_id=payment_id,
        )
