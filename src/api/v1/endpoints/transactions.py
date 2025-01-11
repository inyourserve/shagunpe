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
    EventTransactionsResponse,
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
        # Create transaction
        transaction = await transaction_service.create_online_transaction(
            event_id=data.event_id,
            sender_id=current_user["user_id"],
            data={**data.dict(), "sender_name": current_user.get("name")},
        )

        # Process payment
        payment = await payment_processor.process_payment(
            transaction_id=transaction["id"],
            payment_data={
                "payment_method": data.payment_method,
                "metadata": {
                    "sender_name": current_user.get("name"),
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


@router.get("", response_model=List[TransactionResponse])
async def get_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    type: Optional[str] = Query(None, regex="^(online|cash)$"),
    status: Optional[str] = Query(None, regex="^(pending|completed|failed)$"),
    current_user=Depends(jwt_handler.get_current_user),
):
    """
    Get user's transaction history with filtering options.
    """
    return await transaction_service.get_transactions(
        user_id=current_user["user_id"],
        skip=skip,
        limit=limit,
        type=type,
        status=status,
    )


@router.get("/{transaction_id}", response_model=TransactionDetailResponse)
async def get_transaction_details(
    transaction_id: UUID, current_user=Depends(jwt_handler.get_current_user)
):
    """
    Get detailed information about a specific transaction.
    """
    return await transaction_service.get_transaction_details(
        transaction_id=transaction_id, user_id=current_user["user_id"]
    )


@router.get("/event/{event_id}", response_model=EventTransactionsResponse)
async def get_event_transactions(
    event_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    type: Optional[str] = Query(None, regex="^(online|cash)$"),
    current_user=Depends(jwt_handler.get_current_user),
):
    """
    Get all transactions for a specific event with summary.
    """
    return await transaction_service.get_event_transactions(
        event_id=event_id, skip=skip, limit=limit, type=type
    )


@router.post("/{transaction_id}/verify")
async def verify_transaction(
    transaction_id: UUID,
    verification_data: dict,
    current_user=Depends(jwt_handler.get_current_user),
):
    """
    Verify payment status for online transactions.
    """
    return await transaction_service.update_transaction_status(
        transaction_id=transaction_id,
        status="completed",
        payment_data=verification_data,
    )


@router.get("/{transaction_id}/receipt")
async def get_transaction_receipt(
    transaction_id: UUID, current_user=Depends(jwt_handler.get_current_user)
):
    """
    Generate receipt for a transaction.
    """
    transaction = await transaction_service.get_transaction_details(
        transaction_id=transaction_id, user_id=current_user["user_id"]
    )

    # Add receipt generation logic here
    receipt_data = {
        "transaction_id": transaction["id"],
        "amount": transaction["amount"],
        "sender_name": transaction["sender_name"],
        "event_name": transaction["event_name"],
        "date": transaction["created_at"],
        "type": transaction["type"],
        "status": transaction["status"],
    }

    return receipt_data
