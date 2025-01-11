# src/db/models/transaction.py
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, Dict
from uuid import UUID
from enum import Enum


class TransactionType(str, Enum):
    ONLINE = "online"
    CASH = "cash"


class PaymentMethod(str, Enum):
    UPI = "upi"
    CARD = "card"
    NET_BANKING = "net_banking"


class TransactionStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class OnlineTransactionCreate(BaseModel):
    event_id: UUID = Field(..., description="ID of the event")
    amount: float = Field(..., gt=0, description="Amount to send")
    payment_method: PaymentMethod = Field(..., description="Payment method")
    message: Optional[str] = Field(
        None, max_length=500, description="Optional message with shagun"
    )
    location: Optional[Dict] = Field(None, description="Location details of sender")

    @validator("amount")
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v


class CashTransactionCreate(BaseModel):
    event_id: UUID = Field(..., description="ID of the event")
    amount: float = Field(..., gt=0, description="Amount received")
    sender_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Name of the person who gave shagun",
    )
    address: str = Field(..., max_length=200, description="Address of the sender")
    message: Optional[str] = Field(None, max_length=500, description="Optional message")
    gift_details: Optional[Dict] = Field(None, description="Additional gift details")
    location: Optional[Dict] = Field(None, description="Location coordinates")

    @validator("amount")
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v

    @validator("location")
    def validate_location(cls, v):
        if v and not all(key in v for key in ["latitude", "longitude"]):
            raise ValueError("Location must contain latitude and longitude")
        return v


class TransactionResponse(BaseModel):
    id: UUID
    event_id: UUID
    sender_id: UUID
    receiver_id: UUID
    amount: float
    type: TransactionType
    status: TransactionStatus
    sender_name: Optional[str]
    address: Optional[str]
    message: Optional[str] = None
    location: Optional[Dict]
    gift_details: Optional[Dict]
    upi_ref: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    event_name: Optional[str] = None
    receiver_name: Optional[str] = None
    payment: Optional[Dict] = None

    class Config:
        from_attributes = True


class TransactionDetailResponse(TransactionResponse):
    event_date: Optional[datetime]


class EventTransactionSummary(BaseModel):
    total_count: int
    total_amount: float
    online_amount: float
    cash_amount: float


class EventTransactionsResponse(BaseModel):
    summary: EventTransactionSummary
    transactions: list[TransactionResponse]

    class Config:
        from_attributes = True
