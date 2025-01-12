# src/api/v1/endpoints/sender_details.py
from fastapi import APIRouter, Depends, HTTPException
from src.services.sender_details.service import SenderDetailService
from src.core.security.jwt import jwt_handler
from src.db.models.sender_details import (
    SenderDetailCreate,
    SenderDetailUpdate,
    SenderDetailResponse,
    SenderDetailsListResponse
)
from typing import List
from uuid import UUID
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

sender_detail_service = SenderDetailService()

@router.post("", response_model=SenderDetailResponse)
async def create_sender_detail(
    data: SenderDetailCreate,
    current_user=Depends(jwt_handler.get_current_user)
):
    """Create a new sender detail"""
    return await sender_detail_service.create_sender_detail(
        user_id=current_user['user_id'],
        data=data.dict()
    )

@router.get("", response_model=SenderDetailsListResponse)
async def get_sender_details(
    current_user=Depends(jwt_handler.get_current_user)
):
    """Get all sender details for the current user"""
    return await sender_detail_service.get_sender_details(
        user_id=current_user['user_id']
    )

@router.get("/default", response_model=SenderDetailResponse)
async def get_default_sender_detail(
    current_user=Depends(jwt_handler.get_current_user)
):
    """Get the default sender detail for the current user"""
    return await sender_detail_service.get_default_sender_detail(
        user_id=current_user['user_id']
    )

@router.put("/{id}", response_model=SenderDetailResponse)
async def update_sender_detail(
    id: UUID,
    data: SenderDetailUpdate,
    current_user=Depends(jwt_handler.get_current_user)
):
    """Update a specific sender detail"""
    return await sender_detail_service.update_sender_detail(
        id=id,
        user_id=current_user['user_id'],
        data=data.dict(exclude_unset=True)  # Only include provided fields
    )

@router.delete("/{id}")
async def delete_sender_detail(
    id: UUID,
    current_user=Depends(jwt_handler.get_current_user)
):
    """Delete a specific sender detail"""
    return await sender_detail_service.delete_sender_detail(
        id=id,
        user_id=current_user['user_id']
    )
