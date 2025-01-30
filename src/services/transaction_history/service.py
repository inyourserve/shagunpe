# src/services/transaction/history_service.py
from typing import Dict, Optional
from uuid import UUID
from fastapi import HTTPException
import logging
from src.core.config.database import db

logger = logging.getLogger("shagunpe")


class TransactionHistoryService:
    async def get_user_transactions(
        self,
        user_id: UUID,
        transaction_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> Dict:
        try:
            async with db.pool.acquire() as conn:
                base_query = """
                    FROM transactions t
                    JOIN events e ON t.event_id = e.id
                    WHERE t.status = 'completed'
                    AND (
                        CASE 
                            WHEN $2::text = 'sent' THEN t.sender_id = $1
                            WHEN $2::text = 'received' THEN t.receiver_id = $1
                            ELSE (t.sender_id = $1 OR t.receiver_id = $1)
                        END
                    )
                """
                params = [user_id, transaction_type]

                # Get total count
                count = await conn.fetchval(f"SELECT COUNT(*) {base_query}", *params)

                # Get paginated results with different fields for sent/received
                query = f"""
                    SELECT 
                        t.id,
                        CASE 
                            WHEN t.sender_id = $1 THEN e.guardian_name
                            ELSE t.sender_name
                        END as name,
                        CASE 
                            WHEN t.sender_id = $1 THEN e.village
                            ELSE t.address
                        END as address,
                        e.event_name,
                        t.amount,
                        CASE 
                            WHEN t.sender_id = $1 THEN 'sent'
                            ELSE 'received'
                        END as type,
                        t.created_at,
                        CASE
                            WHEN NOW() - t.created_at < INTERVAL '1 day' 
                                THEN 'Today, ' || to_char(t.created_at, 'HH:MI AM')
                            WHEN NOW() - t.created_at < INTERVAL '2 days'
                                THEN 'Yesterday, ' || to_char(t.created_at, 'HH:MI AM')
                            ELSE to_char(t.created_at, 'DD Mon, HH:MI AM')
                        END as time_ago,
                        CASE 
                            WHEN t.sender_id = $1 THEN t.sender_name
                            ELSE NULL
                        END as sent_by
                    {base_query}
                    ORDER BY t.created_at DESC
                    LIMIT $3 OFFSET $4
                """

                transactions = await conn.fetch(
                    query, *params, page_size, (page - 1) * page_size
                )

                return {
                    "transactions": [
                        {
                            **dict(tx),
                            "amount": float(tx["amount"])
                            * (-1 if tx["type"] == "sent" else 1),
                        }
                        for tx in transactions
                    ],
                    "pagination": {
                        "page": page,
                        "page_size": page_size,
                        "total_count": count,
                        "total_pages": (count + page_size - 1) // page_size,
                        "has_next": page * page_size < count,
                        "has_previous": page > 1,
                    },
                }

        except Exception as e:
            logger.error(f"Error fetching transaction history: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
