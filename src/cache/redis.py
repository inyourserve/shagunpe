# src/cache/redis.py
import redis.asyncio as aioredis
from src.core.config.app import settings
import json


class RedisClient:
    def __init__(self):
        self.redis = None

    async def init(self):
        try:
            self.redis = await aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,  # Automatically decode responses
                socket_timeout=5,  # Connection timeout
                socket_keepalive=True,  # Keep connection alive
            )
            print("Redis connected successfully!")
        except Exception as e:
            print(f"Redis connection error: {str(e)}")
            raise

    async def get(self, key: str):
        value = await self.redis.get(key)
        if value and value.startswith("{"):
            try:
                return json.loads(value)
            except:
                return value
        return value

    async def set(self, key: str, value, expire: int = None):
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        await self.redis.set(key, value, ex=expire)

    async def incr(self, key: str):
        return await self.redis.incr(key)

    async def delete(self, key: str):
        await self.redis.delete(key)

    async def expire(self, key: str, seconds: int):
        await self.redis.expire(key, seconds)

    async def exists(self, key: str):
        return await self.redis.exists(key)

    async def close(self):
        if self.redis:
            await self.redis.close()


redis_client = RedisClient()
