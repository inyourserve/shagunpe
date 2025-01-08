# src/core/security/throttling.py
from fastapi import HTTPException
from datetime import datetime, timedelta
from src.cache.redis import RedisClient


class SecurityThrottling:
    def __init__(self, redis: RedisClient):
        self.redis = redis

    async def check_ip_ban(self, ip: str) -> bool:
        key = f"ip_failures:{ip}"
        failures = await self.redis.get(key) or 0
        return int(failures) >= 5

    async def record_failed_attempt(self, ip: str):
        key = f"ip_failures:{ip}"
        await self.redis.incr(key)
        await self.redis.expire(key, 3600)  # 1 hour ban
