from fastapi import HTTPException
from src.services.notification.msg91 import MSG91Client
from src.core.security.jwt import jwt_handler


class PhoneAuthService:
    def __init__(self):
        self.msg91 = MSG91Client()

    async def send_otp(self, phone: str) -> dict:
        if not await self.msg91.send_otp(phone):
            raise HTTPException(status_code=500, detail="Failed to send OTP")
        return {"message": "OTP sent successfully"}

    async def verify_otp(self, phone: str, otp: str) -> dict:
        if not await self.msg91.verify_otp(phone, otp):
            raise HTTPException(status_code=400, detail="Invalid OTP")

        access_token = jwt_handler.create_access_token(phone)
        return {"access_token": access_token, "token_type": "bearer"}
