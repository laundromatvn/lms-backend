import uuid
from app.core.celery_app import celery_app
from app.core.logging import logger
from app.operations.payment.payment_operation import PaymentOperation
from app.models.payment import PaymentProvider


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
            transaction_code=payment.transaction_code,
        )

        return {
            "success": True,
            "payment_id": payment_id,
            "status": payment.status.value,
            "transaction_code": payment.transaction_code,
            "qr_code": payment.details.get("qr_code") if payment.details else None,
            "expires_at": (
                payment.details.get("expires_at") if payment.details else None
            ),
            "message": "Payment details generated successfully",
        }

    except ValueError as e:
        logger.error(
            f"Payment details generation failed - validation error: {str(e)}",
            payment_id=payment_id,
        )
        return {
            "success": False,
            "payment_id": payment_id,
            "error": "validation_error",
            "message": str(e),
        }

    except Exception as e:
        logger.error(
            f"Payment details generation failed - unexpected error: {str(e)}",
            payment_id=payment_id,
        )


@celery_app.task(name="app.tasks.payment.sync_payment_transaction")
def sync_payment_transaction(
    content: str, status: str, provider: str = PaymentProvider.VIET_QR.value
):
    """
    Generic payment status synchronization task.

    This task updates payment status when payment providers send transaction
    status updates to our system. It's designed to work with any payment provider.

    Args:
        content: order id
        status: Payment status (COMPLETED, FAILED, REFUNDED, etc.)
        provider: Payment provider name (default: VIET_QR)

    Returns:
        Dict containing sync result and updated payment information
    """
    try:
        logger.info(
            f"Starting payment status sync for transaction {content} with status {status}"
        )

        # Process payment status update using the operation
        result = PaymentOperation.update_payment_status_by_transaction_code(
            transaction_code=content, status=status, provider=provider
        )

        logger.info(
            f"Payment status sync completed successfully for transaction {content}",
            payment_id=result.get("payment_id"),
            order_id=result.get("order_id"),
            status=result.get("status"),
        )

        return {
            "success": True,
            "transaction_code": content,
            "payment_id": result.get("payment_id"),
            "order_id": result.get("order_id"),
            "status": result.get("status"),
            "message": "Payment status updated successfully",
        }

    except ValueError as e:
        logger.error(
            f"Payment status sync failed - validation error: {str(e)}",
            transaction_code=content,
            status=status,
        )
        return {
            "success": False,
            "transaction_code": content,
            "error": "validation_error",
            "message": str(e),
        }

    except Exception as e:
        logger.error(
            f"Payment status sync failed - unexpected error: {str(e)}",
            transaction_code=content,
            status=status,
        )
        return {
            "success": False,
            "transaction_code": content,
            "error": "internal_error",
            "message": "Internal server error during payment status sync",
        }
