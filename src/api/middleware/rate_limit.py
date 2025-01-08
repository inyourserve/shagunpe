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
            "default": {"calls": 100, "period": 60},
        }

    async def check_rate_limit(self, request: Request):
        client_ip = request.client.host
        path = request.url.path

        limit_data = self.rate_limits.get(path, self.rate_limits["default"])
        key = f"rate_limit:{client_ip}:{path}"

        count = await self.redis.get(key)
        count = int(count) if count else 0

        if count >= limit_data["calls"]:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "limit": limit_data["calls"],
                    "period": limit_data["period"],
                },
            )

        await self.redis.incr(key)
        if count == 0:
            await self.redis.expire(key, limit_data["period"])
