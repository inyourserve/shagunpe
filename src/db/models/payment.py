# src/db/models/payment.py
from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime
from uuid import UUID
from enum import Enum


class PaymentStatus(str, Enum):
    INITIATED = "initiated"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class PaymentCreate(BaseModel):
    transaction_id: UUID
    amount: float = Field(..., gt=0)
    payment_method: str
    metadata: Optional[Dict] = None


class PaymentResponse(BaseModel):
    id: UUID
    transaction_id: UUID
    amount: float
    payment_method: str
    status: PaymentStatus
    gateway_payment_id: Optional[str]
    gateway_response: Optional[Dict]
    metadata: Optional[Dict]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
