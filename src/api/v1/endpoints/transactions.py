# src/api/v1/endpoints/transactions.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from src.services.transaction.service import TransactionService
from src.services.payment.processor import PaymentProcessor
from src.core.security.jwt import jwt_handler
from src.db.models.transaction import (
    OnlineTransactionCreate,
    CashTransactionCreate,
    TransactionResponse,
    TransactionDetailResponse,
)
from typing import List, Optional
from uuid import UUID
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

transaction_service = TransactionService()
payment_processor = PaymentProcessor()


@router.post("/send", response_model=TransactionResponse)
async def send_shagun(
    data: OnlineTransactionCreate,
    background_tasks: BackgroundTasks,
    current_user=Depends(jwt_handler.get_current_user),
):
    """
    Send online shagun for an event.
    Initiates payment process through payment gateway.
    """
    try:
        # Debug log
        logger.info(f"Received data: {data.dict()}")

        # Create transaction - Don't overwrite sender_name
        transaction = await transaction_service.create_online_transaction(
            event_id=data.event_id,
            sender_id=current_user["user_id"],
            data=data.dict(),  # Use data as is, don't overwrite sender_name
        )

        # Process payment
        payment = await payment_processor.process_payment(
            transaction_id=transaction["id"],
            payment_data={
                "payment_method": data.payment_method,
                "metadata": {
                    "sender_name": data.sender_name,  # Use sender_name from request
                    "event_id": str(data.event_id),
                },
            },
        )

        return {**transaction, "payment": payment}

    except Exception as e:
        logger.error(f"Error in send_shagun: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cash-entry", response_model=TransactionResponse)
async def add_cash_entry(
    data: CashTransactionCreate, current_user=Depends(jwt_handler.get_current_user)
):
    """
    Add cash transaction entry for an event.
    For recording physical cash/gifts received.
    """
    try:
        transaction = await transaction_service.create_cash_transaction(
            event_id=data.event_id, sender_id=current_user["user_id"], data=data.dict()
        )
        return transaction

    except Exception as e:
        logger.error(f"Error in add_cash_entry: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{transaction_id}", response_model=TransactionDetailResponse)
async def get_transaction_detail(
    transaction_id: UUID, current_user=Depends(jwt_handler.get_current_user)
):
    return await TransactionService().get_transaction_detail(
        transaction_id=transaction_id, user_id=current_user["user_id"]
    )
