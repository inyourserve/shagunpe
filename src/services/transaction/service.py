# src/services/transaction/service.py
from fastapi import HTTPException
from typing import Dict, List, Optional
from uuid import UUID
import json
import logging
from datetime import datetime

from src.core.config.database import db

logger = logging.getLogger("shagunpe")


class TransactionService:

    async def create_cash_transaction(
        self, event_id: UUID, sender_id: UUID, data: Dict
    ) -> Dict:
        try:
            async with db.pool.acquire() as conn:
                result = await conn.fetchrow(
                    """
                    WITH event_data AS (
                        SELECT e.id, e.event_name, u.name as creator_name, e.creator_id
                        FROM events e
                        INNER JOIN users u ON e.creator_id = u.id  -- Changed to INNER JOIN
                        WHERE e.id = $1
                        FOR UPDATE
                    ),
                    new_transaction AS (
                        INSERT INTO transactions (
                            event_id, sender_id, receiver_id, amount,
                            type, status, sender_name, address, location,
                            gift_details, message
                        )
                        SELECT 
                            $1, $2, creator_id, $3,
                            'cash', 'completed', $4, $5, $6,
                            $7, $8
                        FROM event_data
                        RETURNING *
                    ),
                    update_event AS (
                        UPDATE events
                        SET total_amount = total_amount + $3,
                            cash_amount = cash_amount + $3,
                            updated_at = NOW()
                        WHERE id = $1
                    )
                    SELECT t.*, 
                           e.event_name,
                           e.creator_name as receiver_name
                    FROM new_transaction t
                    CROSS JOIN event_data e
                    """,
                    event_id,
                    sender_id,
                    data["amount"],
                    data["sender_name"],
                    data.get("address"),
                    json.dumps(data.get("location")) if data.get("location") else None,
                    (
                        json.dumps(data.get("gift_details"))
                        if data.get("gift_details")
                        else None
                    ),
                    data.get("message"),
                )

                if not result:
                    raise HTTPException(status_code=404, detail="Event not found")

                return dict(result)

        except Exception as e:
            logger.error(f"Error creating cash transaction: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    # In TransactionService.create_online_transaction:
    async def create_online_transaction(
        self, event_id: UUID, sender_id: UUID, data: Dict
    ) -> Dict:
        """Create an online transaction with payment initiation"""
        try:
            async with db.pool.acquire() as conn:
                result = await conn.fetchrow(
                    """
                    WITH event_data AS (
                        SELECT e.id, e.event_name, u.name as creator_name, e.creator_id
                        FROM events e
                        INNER JOIN users u ON e.creator_id = u.id
                        WHERE e.id = $1
                        FOR UPDATE
                    )
                    INSERT INTO transactions (
                        event_id, sender_id, receiver_id, amount,
                        type, status, sender_name, address, message, upi_ref
                    )
                    SELECT 
                        $1, $2, creator_id, $3,
                        'online', 'pending', $4, $5, $6, $7
                    FROM event_data
                    RETURNING *
                    """,
                    event_id,
                    sender_id,
                    data["amount"],
                    data.get("sender_name"),  # Added sender_name
                    data.get("address"),  # Added address
                    data.get("message"),
                    data.get("upi_ref"),
                )

                if not result:
                    raise HTTPException(status_code=404, detail="Event not found")

                return dict(result)

        except Exception as e:
            logger.error(f"Error creating online transaction: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_transaction_detail(self, transaction_id: UUID, user_id: UUID) -> Dict:
        """Get detailed information about a specific transaction"""
        try:
            async with db.pool.acquire() as conn:
                transaction = await conn.fetchrow(
                    """
                    SELECT 
                        t.id,
                        t.sender_name,
                        t.address as sender_address,
                        t.amount,
                        t.message,
                        t.location,
                        t.created_at,
                        t.type,
                        e.event_name,
                        e.event_date,
                        CASE 
                            WHEN t.receiver_id = $2 THEN 'Received'
                            WHEN t.sender_id = $2 THEN 'Sent'
                        END as status
                    FROM transactions t
                    JOIN events e ON t.event_id = e.id
                    WHERE t.id = $1 
                    AND (t.sender_id = $2 OR t.receiver_id = $2)
                    """,
                    transaction_id,
                    user_id,
                )

                if not transaction:
                    raise HTTPException(status_code=404, detail="Transaction not found")

                # Format the date & time
                created_at_formatted = transaction["created_at"].strftime(
                    "%d %b %Y, %I:%M %p"
                )

                return {
                    "sender_name": transaction["sender_name"],
                    "sender_address": transaction["sender_address"],
                    "amount": float(transaction["amount"]),
                    "status": transaction["status"],
                    "event_name": transaction["event_name"],
                    "event_date": transaction["event_date"],
                    "location": transaction["location"],
                    "message": transaction["message"],
                    "created_at": created_at_formatted,
                    "type": transaction["type"],
                }

        except Exception as e:
            logger.error(f"Error fetching transaction detail: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
