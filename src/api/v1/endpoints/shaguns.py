# src/api/v1/endpoints/shagun.py
from fastapi import APIRouter, Depends, Query
from typing import Optional
from uuid import UUID
from src.core.security.jwt import jwt_handler
from src.services.shagun.service import ShagunService
from src.db.models.shagun import EventShagunResponse

router = APIRouter()


@router.get("/{event_id}", response_model=EventShagunResponse)
async def get_event_shaguns(
    event_id: UUID,
    search: Optional[str] = Query(None),
    page_online: int = Query(1, ge=1),
    page_cash: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_user=Depends(jwt_handler.get_current_user),
):
    return await ShagunService().get_event_shaguns(
        event_id=event_id,
        search=search,
        page_online=page_online,
        page_cash=page_cash,
        page_size=page_size,
    )
