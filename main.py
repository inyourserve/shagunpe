# Update main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from src.api.middleware.rate_limit import RateLimiter
from src.core.config.app import settings
from src.core.config.database import db
from src.api.v1.endpoints import auth
from src.cache.redis import redis_client
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.limiter = RateLimiter(redis_client)

    async def dispatch(self, request: Request, call_next):
        await self.limiter.check_rate_limit(request)
        response = await call_next(request)
        return response


app = FastAPI(title="ShagunPE")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limiting
app.add_middleware(RateLimitMiddleware)

# Routes
app.include_router(
    auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["Authentication"]
)


@app.on_event("startup")
async def startup():
    await db.initialize()
    await redis_client.init()


@app.on_event("shutdown")
async def shutdown():
    await db.dispose()
    await redis_client.close()
