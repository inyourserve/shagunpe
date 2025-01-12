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
    async def create_online_transaction(self, event_id: UUID, sender_id: UUID, data: Dict) -> Dict:
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
                    data['amount'],
                    data.get('sender_name'),  # Added sender_name
                    data.get('address'),  # Added address
                    data.get('message'),
                    data.get('upi_ref')
                )

                if not result:
                    raise HTTPException(status_code=404, detail="Event not found")

                return dict(result)

        except Exception as e:
            logger.error(f"Error creating online transaction: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_transactions(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
        type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict]:
        """Get user transactions with efficient filtering"""
        try:
            async with db.pool.acquire() as conn:
                # Build query dynamically
                query = """
                    WITH user_transactions AS (
                        SELECT 
                            t.*,
                            e.event_name,
                            sender.name as sender_name,
                            receiver.name as receiver_name,
                            ROW_NUMBER() OVER (ORDER BY t.created_at DESC) as row_num
                        FROM transactions t
                        LEFT JOIN events e ON t.event_id = e.id
                        LEFT JOIN users sender ON t.sender_id = sender.id
                        LEFT JOIN users receiver ON t.receiver_id = receiver.id
                        WHERE (t.sender_id = $1 OR t.receiver_id = $1)
                """
                params = [user_id]

                if type:
                    query += f" AND t.type = ${len(params) + 1}"
                    params.append(type)

                if status:
                    query += f" AND t.status = ${len(params) + 1}"
                    params.append(status)

                query += """
                    )
                    SELECT *
                    FROM user_transactions
                    WHERE row_num > $%d AND row_num <= $%d
                """ % (
                    len(params) + 1,
                    len(params) + 2,
                )

                params.extend([skip, skip + limit])

                rows = await conn.fetch(query, *params)
                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Error fetching transactions: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_transaction_details(
        self, transaction_id: UUID, user_id: UUID
    ) -> Dict:
        """Get detailed transaction information"""
        try:
            async with db.pool.acquire() as conn:
                result = await conn.fetchrow(
                    """
                    SELECT 
                        t.*,
                        e.event_name,
                        e.event_date,
                        sender.name as sender_name,
                        receiver.name as receiver_name
                    FROM transactions t
                    LEFT JOIN events e ON t.event_id = e.id
                    LEFT JOIN users sender ON t.sender_id = sender.id
                    LEFT JOIN users receiver ON t.receiver_id = receiver.id
                    WHERE t.id = $1 AND (t.sender_id = $2 OR t.receiver_id = $2)
                    """,
                    transaction_id,
                    user_id,
                )

                if not result:
                    raise HTTPException(status_code=404, detail="Transaction not found")

                return dict(result)

        except Exception as e:
            logger.error(f"Error fetching transaction details: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def update_transaction_status(
        self, transaction_id: UUID, status: str, payment_data: Optional[Dict] = None
    ) -> Dict:
        """Update transaction status and handle payment completion"""
        try:
            async with db.pool.acquire() as conn:
                async with conn.transaction():
                    transaction = await conn.fetchrow(
                        """
                        UPDATE transactions
                        SET status = $2,
                            updated_at = NOW()
                        WHERE id = $1
                        RETURNING *
                        """,
                        transaction_id,
                        status,
                    )

                    if not transaction:
                        raise HTTPException(
                            status_code=404, detail="Transaction not found"
                        )

                    # If transaction is completed, update event amounts
                    if status == "completed" and transaction["type"] == "online":
                        await conn.execute(
                            """
                            UPDATE events
                            SET total_amount = total_amount + $1,
                                online_amount = online_amount + $1,
                                updated_at = NOW()
                            WHERE id = $2
                            """,
                            transaction["amount"],
                            transaction["event_id"],
                        )

                    return dict(transaction)

        except Exception as e:
            logger.error(f"Error updating transaction status: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_event_transactions(
        self, event_id: UUID, skip: int = 0, limit: int = 20, type: Optional[str] = None
    ) -> Dict:
        """Get transactions for a specific event with summary"""
        try:
            async with db.pool.acquire() as conn:
                # Get summary and transactions in a single query
                query = """
                    WITH summary AS (
                        SELECT 
                            COUNT(*) as total_count,
                            COALESCE(SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END), 0) as total_amount,
                            COALESCE(SUM(CASE WHEN type = 'online' AND status = 'completed' THEN amount ELSE 0 END), 0) as online_amount,
                            COALESCE(SUM(CASE WHEN type = 'cash' THEN amount ELSE 0 END), 0) as cash_amount
                        FROM transactions
                        WHERE event_id = $1
                """
                if type:
                    query += " AND type = $4"

                query += """
                    ),
                    transaction_list AS (
                        SELECT 
                            t.*,
                            sender.name as sender_name,
                            sender.phone as sender_phone
                        FROM transactions t
                        LEFT JOIN users sender ON t.sender_id = sender.id
                        WHERE t.event_id = $1
                """
                if type:
                    query += " AND t.type = $4"

                query += """
                        ORDER BY t.created_at DESC
                        LIMIT $2 OFFSET $3
                    )
                    SELECT 
                        (SELECT ROW_TO_JSON(s.*) FROM summary s) as summary,
                        COALESCE(ARRAY_AGG(ROW_TO_JSON(t.*)), ARRAY[]::JSON[]) as transactions
                    FROM transaction_list t
                """

                params = [event_id, limit, skip]
                if type:
                    params.append(type)

                result = await conn.fetchrow(query, *params)

                return {
                    "summary": result["summary"],
                    "transactions": result["transactions"],
                }

        except Exception as e:
            logger.error(f"Error fetching event transactions: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
