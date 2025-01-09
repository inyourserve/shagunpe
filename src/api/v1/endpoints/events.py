# src/api/v1/endpoints/events.py
from fastapi import APIRouter, Depends, HTTPException
from src.core.security.jwt import jwt_handler, security
from src.services.event.service import EventService
from src.db.models.event import EventCreate, EventResponse
from typing import List
import qrcode
import io
import base64

router = APIRouter()
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
    event_id: str, current_user=Depends(jwt_handler.get_current_user)
):
    """Get QR code for the event"""
    event = await event_service.get_event(event_id, current_user["user_id"])

    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(f"shagunpe://event/{event['shagun_id']}")
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to base64
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    return {
        "qr_code": f"data:image/png;base64,{img_str}",
        "shagun_id": event["shagun_id"],
    }
