# src/services/auth/phone.py
from fastapi import HTTPException
from src.services.notification.msg91 import MSG91Client
from src.core.security.jwt import jwt_handler
from src.core.config.database import db
import logging

logger = logging.getLogger("shagunpe")


class PhoneAuthService:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.msg91 = MSG91Client()

    async def check_user_exists(self, phone: str) -> bool:
        async with db.pool.acquire() as conn:
            user = await conn.fetchrow(
                """
                SELECT id FROM users WHERE phone = $1
                """,
                phone,
            )
            return bool(user)

    async def register_user(self, phone: str):
        async with db.pool.acquire() as conn:
            user = await conn.fetchrow(
                """
                INSERT INTO users (phone, status)
                VALUES ($1, 'active')
                RETURNING id, phone
                """,
                phone,
            )

            await conn.execute(
                """
                INSERT INTO wallets (user_id, balance, hold_balance)
                VALUES ($1, 0, 0)
                """,
                user["id"],
            )

            logger.info(f"New user registered: {phone}")
            return user

    async def send_otp(self, phone: str):
        try:
            logger.debug(f"Sending OTP to {phone}")

            # Check if user exists
            user_exists = await self.check_user_exists(phone)

            # Send OTP via MSG91
            sent = await self.msg91.send_otp(phone)
            if not sent:
                logger.error(f"Failed to send OTP to {phone}")
                raise HTTPException(status_code=500, detail="Failed to send OTP")

            # If new user, register them
            if not user_exists:
                logger.info(f"Registering new user: {phone}")
                await self.register_user(phone)
                message = "User registered and OTP sent successfully"
            else:
                logger.info(f"OTP sent to existing user: {phone}")
                message = "OTP sent successfully"

            return {"message": message, "is_new_user": not user_exists}
        except Exception as e:
            logger.exception(f"Error in send_otp: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def verify_otp(self, phone: str, otp: str):
        try:
            logger.debug(f"Verifying OTP for {phone}")
            verified = await self.msg91.verify_otp(phone, otp)

            if not verified:
                logger.warning(f"Invalid OTP for {phone}")
                raise HTTPException(status_code=400, detail="Invalid OTP")

            async with db.pool.acquire() as conn:
                # Get user
                user = await conn.fetchrow(
                    """
                    SELECT id, phone 
                    FROM users 
                    WHERE phone = $1
                    """,
                    phone,
                )

                if not user:
                    logger.error(f"User not found after OTP verification: {phone}")
                    raise HTTPException(status_code=404, detail="User not found")

                # Update last login
                await conn.execute(
                    """
                    UPDATE users 
                    SET last_login = NOW()
                    WHERE id = $1
                    """,
                    user["id"],
                )

            # Generate token
            token = jwt_handler.create_access_token(
                {"user_id": str(user["id"]), "phone": user["phone"]}
            )

            logger.info(f"User {phone} logged in successfully")
            return {"access_token": token, "token_type": "bearer"}

        except Exception as e:
            logger.exception(f"Error during OTP verification for {phone}")
            raise HTTPException(status_code=500, detail=str(e))
