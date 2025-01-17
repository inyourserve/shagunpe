# src/services/shagun/service.py
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
            type: Optional[str] = None,
            page: int = 1,
            page_size: int = 10
    ) -> Dict:
        try:
            async with db.pool.acquire() as conn:
                # Calculate offset
                offset = (page - 1) * page_size

                # Get event details and summary (unchanged)
                event = await conn.fetchrow(
                    """
                    SELECT 
                        e.id,
                        e.event_name,
                        e.event_date,
                        e.location,
                        COALESCE(SUM(t.amount), 0) as total_shagun,
                        COALESCE(SUM(CASE WHEN t.type = 'online' THEN t.amount ELSE 0 END), 0) as online_shagun,
                        COALESCE(SUM(CASE WHEN t.type = 'cash' THEN t.amount ELSE 0 END), 0) as cash_shagun,
                        COALESCE(COUNT(t.*), 0) as shagun_count,
                        COALESCE(COUNT(CASE WHEN t.type = 'online' THEN 1 END), 0) as online_count,
                        COALESCE(COUNT(CASE WHEN t.type = 'cash' THEN 1 END), 0) as cash_count
                    FROM events e
                    LEFT JOIN transactions t ON e.id = t.event_id AND t.status = 'completed'
                    WHERE e.id = $1
                    GROUP BY e.id
                    """,
                    event_id
                )

                if not event:
                    raise HTTPException(status_code=404, detail="Event not found")

                # Build optimized search query with pagination
                base_query = """
                    FROM transactions t
                    WHERE t.event_id = $1
                """
                params = [event_id]
                param_count = 1

                # Add search conditions if provided
                if search:
                    # Use trigram similarity for faster fuzzy search
                    param_count += 1
                    base_query += f"""
                        AND (
                            t.sender_name ILIKE ${param_count}
                            OR t.address ILIKE ${param_count}
                            OR similarity(t.sender_name, ${param_count}) > 0.3
                        )
                    """
                    params.append(f"%{search}%")

                if type:
                    param_count += 1
                    base_query += f" AND t.type = ${param_count}"
                    params.append(type)

                # Get total count for pagination
                count_query = f"SELECT COUNT(*) {base_query}"
                total_count = await conn.fetchval(count_query, *params)

                # Get paginated results
                query = f"""
                    SELECT 
                        t.id,
                        t.sender_name,
                        t.address as sender_address,
                        t.amount,
                        t.type,
                        t.created_at,
                        t.location,
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
                """ % (param_count + 1, param_count + 2)

                params.extend([page_size, offset])
                shaguns = await conn.fetch(query, *params)

                # Calculate pagination metadata
                total_pages = (total_count + page_size - 1) // page_size
                has_next = page < total_pages
                has_previous = page > 1

                return {
                    "event_name": event["event_name"],
                    "event_date": event["event_date"],
                    "event_location": event["location"],
                    "summary": {
                        "total_shagun": float(event["total_shagun"]),
                        "online_shagun": float(event["online_shagun"]),
                        "cash_shagun": float(event["cash_shagun"]),
                        "shagun_count": int(event["shagun_count"]),
                        "online_count": int(event["online_count"]),
                        "cash_count": int(event["cash_count"])
                    },
                    "shaguns": [
                        {
                            **dict(tx),
                            "amount": float(tx["amount"]),
                            "created_at": tx["created_at"],
                            "time_ago": tx["time_ago"]
                        }
                        for tx in shaguns
                    ],
                    "pagination": {
                        "page": page,
                        "page_size": page_size,
                        "total_count": total_count,
                        "total_pages": total_pages,
                        "has_next": has_next,
                        "has_previous": has_previous
                    }
                }

        except Exception as e:
            logger.error(f"Error fetching event shaguns: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
