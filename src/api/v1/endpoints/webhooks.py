# src/api/v1/endpoints/webhooks.py
from fastapi import APIRouter, Header, Request, HTTPException
from src.services.payment.webhook import WebhookHandler
from src.utils.webhook_utils import WebhookUtils
from src.core.config.app import settings
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

webhook_handler = WebhookHandler()
webhook_utils = WebhookUtils()


@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(..., alias="X-Razorpay-Signature"),
):
    """Handle Razorpay webhook events"""
    try:
        # Get request body
        body = await request.body()

        # Verify signature
        if not webhook_utils.verify_signature(body, x_razorpay_signature):
            return {"status": "invalid_signature"}

        # Check for duplicate webhook
        if await webhook_utils.is_duplicate_webhook(x_razorpay_signature):
            return {"status": "already_processed"}

        # Parse webhook data
        webhook_data = webhook_utils.parse_webhook_data(body)
        if not webhook_data:
            return {"status": "invalid_payload"}

        # Process webhook
        result = await webhook_handler.handle_payment_webhook(
            body=body, signature=x_razorpay_signature
        )

        # Mark as processed if successful
        if result.get("status") == "success":
            await webhook_utils.mark_webhook_processed(x_razorpay_signature)

        return result

    except Exception as e:
        logger.error(f"Webhook processing failed: {str(e)}")
        return {
            "status": "error",
            "message": "Internal server error, but webhook received",
        }


@router.get("/razorpay/test")
async def test_webhook():
    """Simple endpoint to verify webhook setup is working"""
    try:
        return {
            "status": "success",
            "message": "Webhook endpoint is accessible",
            "webhook_url": f"{settings.BASE_URL}/api/v1/webhooks/razorpay",
            "supported_events": [
                "payment.captured",
                "payment.failed",
                "payment.authorized",
                "order.paid",
            ],
        }
    except Exception as e:
        logger.error(f"Test endpoint check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to verify webhook setup")
