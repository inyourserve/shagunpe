# src/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException
from src.services.auth.phone import PhoneAuthService
from src.core.security.jwt import jwt_handler, security
from src.db.models.user import UserCreate

router = APIRouter()
auth_service = PhoneAuthService()


@router.post("/send-otp")
async def send_otp(user: UserCreate):
    return await auth_service.send_otp(user.phone)


@router.post("/verify-otp")
async def verify_otp(phone: str, otp: str):
    return await auth_service.verify_otp(phone, otp)


@router.get("/me")
async def get_current_user(token: str = Depends(security)):
    return jwt_handler.verify_token(token.credentials)
