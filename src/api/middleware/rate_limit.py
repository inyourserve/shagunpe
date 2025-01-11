# src/api/middleware/rate_limit.py
from fastapi import HTTPException, Request
import time
from src.cache.redis import RedisClient


class RateLimiter:
    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client
        self.rate_limits = {
            "/api/v1/auth/send-otp": {"calls": 30, "period": 3600},
            "/api/v1/auth/verify-otp": {"calls": 5, "period": 3600},
            "/api/v1/webhooks/razorpay": {
                "calls": 1000,
                "period": 3600,
            },  # Webhook specific limit
            "default": {"calls": 100, "period": 60},
        }

    async def check_rate_limit(self, request: Request):
        # Skip rate limiting for test webhook endpoint
        if request.url.path == "/api/v1/webhooks/razorpay/test":
            return

        client_ip = request.client.host
        path = request.url.path

        # Get rate limit data for the path
        limit_data = self.rate_limits.get(path, self.rate_limits["default"])

        # Special handling for webhooks - use Razorpay signature if available
        key = f"rate_limit:{client_ip}:{path}"
        if path == "/api/v1/webhooks/razorpay":
            signature = request.headers.get("X-Razorpay-Signature", "")
            if signature:
                key = f"rate_limit:razorpay:{signature}:{path}"

        # Get current count
        count = await self.redis.get(key)
        count = int(count) if count else 0

        # Check if limit exceeded
        if count >= limit_data["calls"]:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "limit": limit_data["calls"],
                    "period": limit_data["period"],
                },
            )

        # Increment counter
        await self.redis.incr(key)
        if count == 0:
            await self.redis.expire(key, limit_data["period"])

    async def increment_webhook_count(self, signature: str, path: str) -> None:
        """Specific method to track webhook calls"""
        key = f"webhook_count:razorpay:{signature}:{path}"
        await self.redis.incr(key)
        await self.redis.expire(key, 86400)  # 24 hours retention

    async def get_webhook_count(self, signature: str, path: str) -> int:
        """Get webhook call count for a signature"""
        key = f"webhook_count:razorpay:{signature}:{path}"
        count = await self.redis.get(key)
        return int(count) if count else 0
