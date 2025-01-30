# src/api/v1/endpoints/transaction.py
from fastapi import APIRouter, Depends, Query
from typing import Optional
from uuid import UUID
from src.core.security.jwt import jwt_handler
from src.services.transaction_history.service import TransactionHistoryService
from src.db.models.transaction_history import TransactionHistoryResponse

router = APIRouter()


@router.get("/history", response_model=TransactionHistoryResponse)
async def get_transaction_history(
    transaction_type: Optional[str] = Query(
        None, regex="^(sent|received)$", description="Filter by transaction type"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=50, description="Items per page"),
    current_user=Depends(jwt_handler.get_current_user),
):
    """
    Get transaction history for the current user.

    - Filter by type: sent/received/all
    - Pagination support
    - Sorted by date (newest first)
    """
    return await TransactionHistoryService().get_user_transactions(
        user_id=current_user["user_id"],
        transaction_type=transaction_type,
        page=page,
        page_size=page_size,
    )
