# src/utils/webhook_utils.py
from src.cache.redis import RedisClient
from typing import Dict, Optional
import hmac
import hashlib
from src.core.config.app import settings
import json
import logging

logger = logging.getLogger("shagunpe")
redis = RedisClient()


class WebhookUtils:
    @staticmethod
    def verify_signature(body: bytes, signature: str) -> bool:
        """Verify Razorpay webhook signature"""
        try:
            expected = hmac.new(
                settings.RAZORPAY_WEBHOOK_SECRET.encode(), body, hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(expected, signature)
        except Exception as e:
            logger.error(f"Signature verification failed: {str(e)}")
            return False

    @staticmethod
    def parse_webhook_data(body: bytes) -> Optional[Dict]:
        """Parse webhook request body"""
        try:
            payload = json.loads(body)
            event = payload.get("event")

            # Handle both payment and order events
            if event.startswith("payment."):
                entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
            elif event == "order.paid":
                entity = payload.get("payload", {}).get("order", {}).get("entity", {})
            else:
                entity = {}

            return {
                "event": event,
                "order_id": entity.get("order_id")
                or entity.get("id"),  # order.id for order events
                "payment_id": entity.get("id"),
                "amount": entity.get("amount", 0),
                "raw_payload": payload,
            }
        except json.JSONDecodeError:
            logger.error("Invalid JSON in webhook payload")
            return None
        except Exception as e:
            logger.error(f"Error parsing webhook data: {str(e)}")
            return None

    @staticmethod
    async def is_duplicate_webhook(signature: str) -> bool:
        """Check if webhook was already processed"""
        key = f"webhook:processed:{signature}"
        return await redis.exists(key)

    @staticmethod
    async def mark_webhook_processed(signature: str, expiry: int = 3600):
        """Mark webhook as processed"""
        key = f"webhook:processed:{signature}"
        await redis.set(key, "1", expiry)
