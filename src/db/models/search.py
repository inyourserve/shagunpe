# src/db/models/search.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from uuid import UUID


class ShagunSearchItem(BaseModel):
    id: UUID
    sender_name: str
    sender_address: Optional[str]
    amount: float
    type: str
    created_at: datetime
    time_ago: str
    location: Optional[str]

    class Config:
        from_attributes = True


class SearchPagination(BaseModel):
    page: int
    page_size: int
    total_count: int
    total_pages: int
    has_next: bool
    has_previous: bool


class ShagunSearchResponse(BaseModel):
    results: List[ShagunSearchItem]
    pagination: SearchPagination

    class Config:
        from_attributes = True
