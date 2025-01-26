from typing import Dict, Optional
from uuid import UUID
from fastapi import HTTPException
import logging

from src.core.config.database import db

logger = logging.getLogger("shagunpe")


class ShagunService:
    async def get_event_shaguns(
        self,
        event_id: UUID,
        search: Optional[str] = None,
        page_online: int = 1,
        page_cash: int = 1,
        page_size: int = 10,
    ) -> Dict:
        try:
            async with db.pool.acquire() as conn:
                event = await conn.fetchrow(
                    """
                   SELECT 
                       e.id, e.event_name, e.event_date, e.location,
                       COALESCE(SUM(t.amount), 0) as total_shagun,
                       COALESCE(SUM(CASE WHEN t.type = 'online' THEN t.amount ELSE 0 END), 0) as online_shagun,
                       COALESCE(SUM(CASE WHEN t.type = 'cash' THEN t.amount ELSE 0 END), 0) as cash_shagun,
                       COUNT(t.*) as shagun_count,
                       COUNT(CASE WHEN t.type = 'online' THEN 1 END) as online_count,
                       COUNT(CASE WHEN t.type = 'cash' THEN 1 END) as cash_count
                   FROM events e
                   LEFT JOIN transactions t ON e.id = t.event_id AND t.status = 'completed'
                   WHERE e.id = $1
                   GROUP BY e.id
               """,
                    event_id,
                )

                if not event:
                    raise HTTPException(status_code=404, detail="Event not found")

                async def get_shaguns_by_type(type: str, page: int):
                    offset = (page - 1) * page_size
                    base_query = """
                       FROM transactions t 
                       WHERE t.event_id = $1 AND t.type = $2
                       AND t.status = 'completed'
                       
                   """
                    params = [event_id, type]

                    if search:
                        base_query += """
                           AND (
                               t.sender_name ILIKE $3 
                               OR t.address ILIKE $3
                               OR similarity(t.sender_name, $3) > 0.3
                           )
                       """
                        params.append(f"%{search}%")

                    total_count = await conn.fetchval(
                        f"SELECT COUNT(*) {base_query}", *params
                    )

                    shaguns = await conn.fetch(
                        f"""
                       SELECT 
                           t.id, t.sender_name, t.address as sender_address,
                           t.amount, t.type, t.created_at, t.location,
                           CASE
                               WHEN NOW() - t.created_at < INTERVAL '1 hour' 
                                   THEN EXTRACT(MINUTE FROM NOW() - t.created_at)::TEXT || ' min ago'
                               WHEN NOW() - t.created_at < INTERVAL '24 hours' 
                                   THEN EXTRACT(HOUR FROM NOW() - t.created_at)::TEXT || 'h ago'
                               WHEN NOW() - t.created_at < INTERVAL '7 days' 
                                   THEN EXTRACT(DAY FROM NOW() - t.created_at)::TEXT || 'd ago'
                               ELSE to_char(t.created_at, 'DD Mon YYYY')
                           END as time_ago
                       {base_query}
                       ORDER BY t.created_at DESC
                       LIMIT $%d OFFSET $%d
                   """
                        % (len(params) + 1, len(params) + 2),
                        *params,
                        page_size,
                        offset,
                    )

                    return {
                        "items": [
                            {
                                **dict(tx),
                                "amount": float(tx["amount"]),
                                "created_at": tx["created_at"],
                                "time_ago": tx["time_ago"],
                            }
                            for tx in shaguns
                        ],
                        "pagination": {
                            "page": page,
                            "page_size": page_size,
                            "total_count": total_count,
                            "total_pages": (total_count + page_size - 1) // page_size,
                            "has_next": page * page_size < total_count,
                            "has_previous": page > 1,
                        },
                    }

                online_shaguns = await get_shaguns_by_type("online", page_online)
                cash_shaguns = await get_shaguns_by_type("cash", page_cash)

                return {
                    "event_name": event["event_name"],
                    "event_date": event["event_date"],
                    "event_location": event["location"],
                    "summary": {
                        "total_shagun": float(event["total_shagun"]),
                        "online_shagun": float(event["online_shagun"]),
                        "cash_shagun": float(event["cash_shagun"]),
                        "shagun_count": event["shagun_count"],
                        "online_count": event["online_count"],
                        "cash_count": event["cash_count"],
                    },
                    "online_shaguns": online_shaguns,
                    "cash_shaguns": cash_shaguns,
                }

        except Exception as e:
            logger.error(f"Error fetching event shaguns: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
