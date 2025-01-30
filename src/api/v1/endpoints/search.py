# src/api/v1/endpoints/search.py
from fastapi import APIRouter, Depends, Query
from uuid import UUID
from src.core.security.jwt import jwt_handler
from src.services.search.service import SearchService
from src.db.models.search import ShagunSearchResponse

router = APIRouter()


@router.get("/search/{event_id}", response_model=ShagunSearchResponse)
async def search_shaguns(
    event_id: UUID,
    q: str = Query(..., min_length=2, description="Search query"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_user=Depends(jwt_handler.get_current_user),
):
    return await SearchService().search_shaguns(
        event_id=event_id, query=q, page=page, page_size=page_size
    )
