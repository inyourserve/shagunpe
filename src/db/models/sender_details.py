# src/db/models/sender_detail.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from uuid import UUID

class SenderDetailCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    address: str = Field(..., min_length=5, max_length=200)
    is_default: Optional[bool] = Field(False, description="Set as default sender detail")

class SenderDetailUpdate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    address: str = Field(..., min_length=5, max_length=200)
    is_default: Optional[bool] = Field(None, description="Set as default sender detail")

class SenderDetailResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    address: str
    is_default: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class SenderDetailsListResponse(BaseModel):
    count: int
    data: List[SenderDetailResponse]
    message: str

    class Config:
        from_attributes = True
