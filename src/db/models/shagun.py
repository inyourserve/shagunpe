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


class PaginationInfo(BaseModel):
    page: int
    page_size: int
    total_count: int
    total_pages: int
    has_next: bool
    has_previous: bool


class PaginatedShaguns(BaseModel):
    items: List[ShagunListItem]
    pagination: PaginationInfo


class EventShagunResponse(BaseModel):
    event_name: str
    event_date: datetime
    event_location: Optional[str]
    summary: ShagunSummary
    online_shaguns: PaginatedShaguns
    cash_shaguns: PaginatedShaguns

    class Config:
        from_attributes = True
