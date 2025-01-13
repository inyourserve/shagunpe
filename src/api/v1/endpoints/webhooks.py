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
        x_razorpay_signature: str = Header(..., alias="X-Razorpay-Signature")
):
    """Handle Razorpay webhook events"""
    try:
        body = await request.body()
        result = await webhook_handler.handle_payment_webhook(
            body=body,
            signature=x_razorpay_signature
        )
        return result

    except Exception as e:
        logger.error(f"Webhook processing failed: {str(e)}")
        # Always return 200 for webhooks
        return {
            "status": "error",
            "message": "Internal server error, but webhook received"
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
        "mode": "test" if settings.PAYMENT_TEST_MODE else "live",
    }
