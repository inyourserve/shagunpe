from typing import Dict
from uuid import UUID
from fastapi import HTTPException
import logging
from src.core.config.database import db

logger = logging.getLogger("shagunpe")


class SearchService:
    async def search_shaguns(
        self,
        event_id: UUID,
        query: str,
        page: int = 1,
        page_size: int = 10,
    ) -> Dict:
        try:
            async with db.pool.acquire() as conn:
                # Single optimized query using ILIKE
                base_query = """
                    FROM transactions t 
                    WHERE t.event_id = $1 
                    AND t.status = 'completed'
                    AND (
                        t.sender_name ILIKE $2
                        OR t.address ILIKE $2
                    )
                """
                params = [event_id, f"%{query}%"]

                # Get total count and results in one query for better performance
                results = await conn.fetch(
                    f"""
                    WITH matched_results AS (
                        SELECT 
                            t.id, 
                            t.sender_name,
                            t.address as sender_address,
                            t.amount,
                            t.type,
                            t.created_at,
                            t.location,
                            COUNT(*) OVER() as total_count
                        {base_query}
                        ORDER BY t.created_at DESC
                        LIMIT $3 OFFSET $4
                    )
                    SELECT *, 
                        CASE
                            WHEN NOW() - created_at < INTERVAL '1 hour' 
                                THEN EXTRACT(MINUTE FROM NOW() - created_at)::TEXT || ' min ago'
                            WHEN NOW() - created_at < INTERVAL '24 hours' 
                                THEN EXTRACT(HOUR FROM NOW() - created_at)::TEXT || 'h ago'
                            WHEN NOW() - created_at < INTERVAL '7 days' 
                                THEN EXTRACT(DAY FROM NOW() - created_at)::TEXT || 'd ago'
                            ELSE to_char(created_at, 'DD Mon YYYY')
                        END as time_ago
                    FROM matched_results
                """,
                    *params,
                    page_size,
                    (page - 1) * page_size,
                )

                total_count = results[0]["total_count"] if results else 0

                return {
                    "results": [
                        {
                            **dict(tx),
                            "total_count": None,  # Remove total_count from individual results
                        }
                        for tx in results
                    ],
                    "pagination": {
                        "page": page,
                        "page_size": page_size,
                        "total_count": total_count,
                        "total_pages": (total_count + page_size - 1) // page_size,
                        "has_next": (page * page_size) < total_count,
                        "has_previous": page > 1,
                    },
                }

        except Exception as e:
            logger.error(f"Error in search: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
