# src/api/v1/endpoints/webhooks.py
from fastapi import APIRouter, HTTPException, Request, Header
from src.services.payment.processor import PaymentProcessor
from src.core.config.app import settings
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

payment_processor = PaymentProcessor()


@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(..., alias="X-Razorpay-Signature"),
):
    """
    Handle Razorpay webhooks for payment status updates
    Webhook URL to be configured in Razorpay Dashboard:
    your_domain/api/v1/webhooks/razorpay
    """
    try:
        # Get raw request body
        body = await request.body()

        # Verify webhook signature
        is_valid = payment_processor.gateway.client.utility.verify_webhook_signature(
            body.decode(), x_razorpay_signature, settings.RAZORPAY_WEBHOOK_SECRET
        )

        if not is_valid:
            logger.error("Invalid webhook signature")
            raise HTTPException(status_code=400, detail="Invalid signature")

        # Process webhook data
        webhook_data = await request.json()

        # Extract payment details
        event = webhook_data.get("event")
        payment_id = (
            webhook_data.get("payload", {})
            .get("payment", {})
            .get("entity", {})
            .get("order_id")
        )

        if not payment_id:
            logger.error("Payment ID not found in webhook data")
            raise HTTPException(status_code=400, detail="Invalid webhook data")

        # Map Razorpay status to our status
        status_mapping = {
            "payment.captured": "completed",
            "payment.failed": "failed",
            "payment.authorized": "processing",
        }

        status = status_mapping.get(event, "pending")

        # Update payment status
        await payment_processor.update_payment_status(
            payment_id=payment_id, status=status, webhook_data=webhook_data
        )

        return {"status": "success"}

    except Exception as e:
        logger.error(f"Webhook processing failed: {str(e)}")
        # Always return 200 to Razorpay even if processing fails
        # This prevents webhook retries for errors we can't fix
        return {"status": "received"}


@router.post("/razorpay/test")
async def test_webhook():
    """
    Test endpoint for webhook integration
    """
    return {"status": "success", "message": "Webhook endpoint is working"}
