from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from src.core.config.database import db
from src.services.auth.phone import PhoneAuthService
from src.core.security.jwt import jwt_handler, security
from src.db.models.user import UserCreate
from src.cache.redis import redis_client
import logging

# Get logger
logger = logging.getLogger("shagunpe")

router = APIRouter()
auth_service = PhoneAuthService(redis_client=redis_client)


@router.post("/send-otp")
async def send_otp(user: UserCreate):
    logger.debug(f"Sending OTP to {user.phone}")
    return await auth_service.send_otp(user.phone)


@router.post("/verify-otp")
async def verify_otp(phone: str, otp: str):
    logger.debug(f"Verifying OTP for {phone}")
    return await auth_service.verify_otp(phone, otp)


@router.get("/me")
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    try:
        payload = jwt_handler.verify_token(credentials.credentials)

        async with db.pool.acquire() as conn:
            user = await conn.fetchrow(
                """
                SELECT u.*, w.balance, w.hold_balance
                FROM users u
                LEFT JOIN wallets w ON w.user_id = u.id
                WHERE u.id = $1
                """,
                payload["user_id"],
            )

            if not user:
                logger.warning(f"User not found: {payload['user_id']}")
                raise HTTPException(status_code=404, detail="User not found")

            user_data = dict(user)
            if user_data.get("balance"):
                user_data["balance"] = float(user_data["balance"])
            if user_data.get("hold_balance"):
                user_data["hold_balance"] = float(user_data["hold_balance"])

            logger.debug(f"User details retrieved: {payload['user_id']}")
            return user_data

    except Exception as e:
        logger.exception("Error retrieving user details")
        raise HTTPException(status_code=500, detail="Internal server error")
