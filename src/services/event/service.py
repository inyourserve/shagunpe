from fastapi import HTTPException
from src.core.config.database import db
from src.db.models.event import EventCreate
import shortuuid
import logging

logger = logging.getLogger("shagunpe")


class EventService:
    def __init__(self):
        pass

    async def create_event(self, event_data: EventCreate, user_id: str):
        try:
            async with db.pool.acquire() as conn:
                # Generate unique shagun_id
                shagun_id = f"SG{shortuuid.uuid()[:8].upper()}"

                event = await conn.fetchrow(
                    """
                    INSERT INTO events 
                    (creator_id, event_name, guardian_name, event_date, 
                     village, location, shagun_id)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING *
                    """,
                    user_id,
                    event_data.event_name,
                    event_data.guardian_name,
                    event_data.event_date,
                    event_data.village,
                    event_data.location,
                    shagun_id,
                )

                return dict(event)
        except Exception as e:
            logger.error(f"Error creating event: {str(e)}")
            raise HTTPException(status_code=500, detail="Error creating event")

    async def get_events(self, user_id: str):
        try:
            async with db.pool.acquire() as conn:
                events = await conn.fetch(
                    """
                    SELECT e.*, u.name as creator_name
                    FROM events e
                    LEFT JOIN users u ON e.creator_id = u.id
                    WHERE e.creator_id = $1
                    ORDER BY e.event_date DESC
                    """,
                    user_id,
                )
                return [dict(event) for event in events]
        except Exception as e:
            logger.error(f"Error fetching events: {str(e)}")
            raise HTTPException(status_code=500, detail="Error fetching events")

    async def get_event(self, event_id: str, user_id: str):
        try:
            async with db.pool.acquire() as conn:
                event = await conn.fetchrow(
                    """
                    SELECT e.*, u.name as creator_name,
                           COUNT(DISTINCT t.id) as transaction_count,
                           COALESCE(SUM(t.amount), 0) as total_received
                    FROM events e
                    LEFT JOIN users u ON e.creator_id = u.id
                    LEFT JOIN transactions t ON e.id = t.event_id
                    WHERE e.id = $1 AND e.creator_id = $2
                    GROUP BY e.id, u.name
                    """,
                    event_id,
                    user_id,
                )

                if not event:
                    raise HTTPException(status_code=404, detail="Event not found")

                return dict(event)
        except Exception as e:
            logger.error(f"Error fetching event: {str(e)}")
            raise HTTPException(status_code=500, detail="Error fetching event")
