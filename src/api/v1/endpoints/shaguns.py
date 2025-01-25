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
    search: Optional[str] = Query(None, description="Search by sender name or address"),
    type: Optional[str] = Query(
        None, regex="^(online|cash)$", description="Filter by shagun type"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=50, description="Items per page"),
    current_user=Depends(jwt_handler.get_current_user),
):
    return await ShagunService().get_event_shaguns(
        event_id=event_id, search=search, type=type, page=page, page_size=page_size
    )
