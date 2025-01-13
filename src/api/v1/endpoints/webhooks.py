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
        # Log webhook receipt
        logger.info("Received Razorpay webhook")

        # Get and log request body
        body = await request.body()

        # Verify signature
        if not webhook_utils.verify_signature(body, x_razorpay_signature):
            logger.warning("Invalid webhook signature")
            return {"status": "invalid_signature"}

        # Check for duplicate webhook
        if await webhook_utils.is_duplicate_webhook(x_razorpay_signature):
            logger.info("Duplicate webhook received")
            return {"status": "already_processed"}

        # Parse webhook data
        webhook_data = webhook_utils.parse_webhook_data(body)
        if not webhook_data:
            logger.error("Failed to parse webhook data")
            return {"status": "invalid_payload"}

        # Log webhook details
        logger.info(
            f"Processing webhook: order_id={webhook_data.get('order_id')}, event={webhook_data.get('event')}"
        )

        # Process webhook
        result = await webhook_handler.handle_payment_webhook(
            body=body, signature=x_razorpay_signature
        )

        # Log result
        logger.info(f"Webhook processing result: {result}")

        # Mark as processed if successful
        if result.get("status") == "success":
            await webhook_utils.mark_webhook_processed(x_razorpay_signature)

        return result

    except Exception as e:
        logger.error(f"Webhook processing failed: {str(e)}")
        # Always return 200 to acknowledge receipt
        return {
            "status": "error",
            "message": "Internal server error, but webhook received",
        }


@router.get("/razorpay/test")
async def test_webhook():
    """Test if webhook endpoint is accessible"""
    try:
        webhook_url = f"{settings.BASE_URL}/api/v1/webhooks/razorpay"
        logger.info(f"Testing webhook accessibility: {webhook_url}")

        return {
            "status": "success",
            "message": "Webhook endpoint is accessible",
            "webhook_url": webhook_url,
            "supported_events": [
                "payment.captured",  # Payment successful
                "payment.failed",  # Payment failed
                "payment.authorized",  # Payment authorized but not captured
                "order.paid",  # Order marked as paid
            ],
        }
    except Exception as e:
        logger.error(f"Webhook test failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to verify webhook setup")


# Optional: Add health check endpoint
@router.get("/razorpay/health")
async def webhook_health():
    """Check webhook endpoint health"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "mode": "test" if settings.PAYMENT_TEST_MODE else "live",
    }
