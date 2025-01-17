# src/db/models/shagun.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from uuid import UUID


class ShagunSummary(BaseModel):
    total_shagun: float
    online_shagun: float
    cash_shagun: float
    shagun_count: int
    online_count: int
    cash_count: int


class ShagunListItem(BaseModel):
    id: UUID
    sender_name: str
    sender_address: Optional[str]
    amount: float
    type: str
    created_at: datetime
    location: Optional[str]

    class Config:
        from_attributes = True


class EventShagunResponse(BaseModel):
    event_name: str
    event_date: datetime
    event_location: Optional[str]
    summary: ShagunSummary
    shaguns: List[ShagunListItem]

    class Config:
        from_attributes = True
