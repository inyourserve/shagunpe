# src/db/models/transaction_history.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from uuid import UUID


class TransactionHistoryItem(BaseModel):
    id: UUID
    name: str  # Guardian name for sent, sender_name for received
    address: str  # Event location for sent, sender address for received
    event_name: str
    amount: float
    type: str  # 'sent' or 'received'
    created_at: datetime
    time_ago: str
    sent_by: Optional[str]

    class Config:
        from_attributes = True


class PaginationInfo(BaseModel):
    page: int
    page_size: int
    total_count: int
    total_pages: int
    has_next: bool
    has_previous: bool


class TransactionHistoryResponse(BaseModel):
    transactions: List[TransactionHistoryItem]
    pagination: PaginationInfo

    class Config:
        from_attributes = True
