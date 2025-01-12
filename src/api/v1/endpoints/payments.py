# src/api/v1/endpoints/payments.py
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from src.services.payment.processor import PaymentProcessor
from src.core.security.jwt import jwt_handler
from src.db.models.payment import PaymentVerificationData
from typing import Optional
from uuid import UUID
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

payment_processor = PaymentProcessor()


@router.post("/verify")
async def verify_payment(
    payment_data: PaymentVerificationData,
    current_user=Depends(jwt_handler.get_current_user)
):
    """
    Verify Razorpay payment
    - razorpay_order_id: The order ID received when creating transaction
    - razorpay_payment_id: Payment ID received after successful payment
    - razorpay_signature: Signature received after successful payment
    """
    try:
        return await payment_processor.verify_payment(
            payment_id=payment_data.razorpay_order_id,
            verification_data=payment_data.dict()
        )
    except Exception as e:
        logger.error(f"Payment verification failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))



@router.get("/{payment_id}")
async def get_payment_status(
    payment_id: UUID, current_user=Depends(jwt_handler.get_current_user)
):
    """Get payment status and details"""
    try:
        return await payment_processor.get_payment_details(str(payment_id))
    except Exception as e:
        logger.error(f"Failed to get payment details: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
