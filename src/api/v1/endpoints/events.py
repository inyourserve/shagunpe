# src/api/v1/endpoints/events.py
from fastapi import APIRouter, Depends, HTTPException
import logging
from src.core.security.jwt import jwt_handler, security
from src.services.event.service import EventService
from src.db.models.event import EventCreate, EventResponse
from typing import List
import qrcode
import io
import base64

router = APIRouter()
logger = logging.getLogger(__name__)
event_service = EventService()


@router.post("/events", response_model=EventResponse)
async def create_event(
    event_data: EventCreate, current_user=Depends(jwt_handler.get_current_user)
):
    """Create a new event"""
    return await event_service.create_event(event_data, current_user["user_id"])


@router.get("/events", response_model=List[EventResponse])
async def get_events(current_user=Depends(jwt_handler.get_current_user)):
    """Get all events for the user"""
    return await event_service.get_events(current_user["user_id"])


@router.get("/events/{event_id}", response_model=EventResponse)
async def get_event(event_id: str, current_user=Depends(jwt_handler.get_current_user)):
    """Get specific event details"""
    return await event_service.get_event(event_id, current_user["user_id"])


@router.get("/events/{event_id}/qr")
async def get_event_qr(
    event_id: str,
    force_refresh: bool = False,
    current_user=Depends(jwt_handler.get_current_user),
):
    """Get QR code for event"""
    # First verify user has access to this event
    event = await event_service.get_event(event_id, current_user["user_id"])

    # Get or generate QR
    qr_data = await event_service.qr_generator.get_qr(event_id, force_refresh)

    return {
        "qr_code": qr_data,
        "shagun_id": event["shagun_id"],
        "event_name": event["event_name"],
    }
