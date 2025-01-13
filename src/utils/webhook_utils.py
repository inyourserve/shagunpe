# src/utils/webhook_utils.py
from src.cache.redis import RedisClient
from typing import Dict, Optional
import hmac
import hashlib
from src.core.config.app import settings
import json
import logging

logger = logging.getLogger("shagunpe")


class WebhookUtils:
    def __init__(self):
        self.redis = RedisClient()

    def verify_signature(self, body: bytes, signature: str) -> bool:
        """Verify Razorpay webhook signature"""
        try:
            expected = hmac.new(
                settings.RAZORPAY_WEBHOOK_SECRET.encode(), body, hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(expected, signature)
        except Exception as e:
            logger.error(f"Signature verification failed: {str(e)}")
            return False

    def parse_webhook_data(self, body: bytes) -> Optional[Dict]:
        """Parse webhook request body"""
        try:
            payload = json.loads(body)
            event = payload.get("event")

            # Handle both payment and order events
            if event.startswith("payment."):
                entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
            else:
                entity = {}

            return {
                "event": event,
                "order_id": entity.get("order_id"),
                "payment_id": entity.get("id"),
                "amount": entity.get("amount", 0),
                "status": entity.get("status"),
                "raw_payload": payload,
            }
        except Exception as e:
            logger.error(f"Error parsing webhook data: {str(e)}")
            return None

    async def is_duplicate_webhook(self, signature: str) -> bool:
        """Check if webhook was already processed"""
        key = f"webhook:processed:{signature}"
        return bool(await self.redis.exists(key))

    async def mark_webhook_processed(self, signature: str):
        """Mark webhook as processed with 24hr expiry"""
        key = f"webhook:processed:{signature}"
        await self.redis.set(key, "1", ex=86400)  # 24 hours expiry
