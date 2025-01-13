# src/utils/webhook_utils.py
from src.cache.redis import redis_client
import hmac
import hashlib
from src.core.config.app import settings
import logging

logger = logging.getLogger("shagunpe")

class WebhookUtils:
    WEBHOOK_EXPIRY = 86400  # 24 hours
    RATE_LIMIT_WINDOW = 60  # 1 minute
    MAX_WEBHOOKS_PER_MINUTE = 100

    @staticmethod
    def verify_signature(body: bytes, signature: str) -> bool:
        """Verify Razorpay webhook signature"""
        try:
            expected = hmac.new(
                settings.RAZORPAY_WEBHOOK_SECRET.encode(),
                body,
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(expected, signature)
        except Exception as e:
            logger.error(f"Signature verification failed: {str(e)}")
            return False

    @staticmethod
    async def is_duplicate_webhook(signature: str) -> bool:
        """Check if webhook was already processed"""
        key = f"webhook:processed:{signature}"
        try:
            return await redis_client.exists(key)
        except Exception as e:
            logger.error(f"Redis check failed: {str(e)}")
            return False

    @staticmethod
    async def mark_webhook_processed(signature: str):
        """Mark webhook as processed"""
        key = f"webhook:processed:{signature}"
        try:
            await redis_client.set(key, "1", ex=WebhookUtils.WEBHOOK_EXPIRY)
        except Exception as e:
            logger.error(f"Redis mark failed: {str(e)}")

    @staticmethod
    async def check_rate_limit(signature: str) -> bool:
        """Check webhook rate limit"""
        key = f"webhook:rate:{signature}"
        try:
            count = await redis_client.incr(key)
            if count == 1:
                await redis_client.expire(key, WebhookUtils.RATE_LIMIT_WINDOW)
            return count <= WebhookUtils.MAX_WEBHOOKS_PER_MINUTE
        except Exception as e:
            logger.error(f"Rate limit check failed: {str(e)}")
            return True  # Allow on Redis failure
