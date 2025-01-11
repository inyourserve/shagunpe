# Update main.py
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from src.api.middleware.rate_limit import RateLimiter
from src.core.config.app import settings
from src.core.config.database import db
from src.api.v1.endpoints import auth
from src.api.v1.endpoints import events, transactions, payments, webhooks
from src.cache.redis import redis_client
from starlette.middleware.base import BaseHTTPMiddleware

os.makedirs("logs", exist_ok=True)


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


app.include_router(
    events.router, prefix=f"{settings.API_V1_PREFIX}/events", tags=["Events"]
)

app.include_router(
    transactions.router,
    prefix=f"{settings.API_V1_PREFIX}/transactions",
    tags=["Transactions"],
)

app.include_router(
    payments.router, prefix=f"{settings.API_V1_PREFIX}/payments", tags=["Payments"]
)

app.include_router(
    webhooks.router, prefix=f"{settings.API_V1_PREFIX}/webhooks", tags=["Webhooks"]
)


@app.on_event("startup")
async def startup():
    await db.initialize()
    await redis_client.init()


@app.on_event("shutdown")
async def shutdown():
    await db.dispose()
    await redis_client.close()
