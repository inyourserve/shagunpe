# src/db/models/event.py
from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional
from uuid import UUID


class EventCreate(BaseModel):
    event_name: str = Field(..., min_length=3, max_length=200)
    guardian_name: Optional[str] = Field(None, max_length=100)
    event_date: date
    village: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=200)


class EventResponse(BaseModel):
    id: UUID
    event_name: str
    guardian_name: Optional[str]
    event_date: date
    village: Optional[str]
    location: Optional[str]
    shagun_id: str
    total_amount: float
    online_amount: float
    cash_amount: float
    status: str
    created_at: datetime


class EventQRResponse(BaseModel):
    event_id: str
    event_name: str
    event_date: date
    village: Optional[str]
    qr_code: str
    shagun_id: str
    status: str
    created_at: datetime


class EventByShagunIDResponse(BaseModel):
    event_id: UUID
    event_name: str
    event_date: date
    village: Optional[str]
    guardian_name: Optional[str]
    status: str
    created_at: datetime
