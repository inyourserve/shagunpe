# src/services/sender_detail/service.py
from fastapi import HTTPException
from typing import List, Dict, Optional
from uuid import UUID
import logging
from src.core.config.database import db
from src.core.errors.base import NotFoundError, ValidationError

logger = logging.getLogger("shagunpe")


class SenderDetailService:
    async def _ensure_single_default(
        self, conn, user_id: UUID, exclude_id: Optional[UUID] = None
    ) -> None:
        """Ensure only one default sender detail exists for a user"""
        query = """
            SELECT COUNT(*) FROM sender_details 
            WHERE user_id = $1 AND is_default = true
        """
        params = [user_id]

        if exclude_id:
            query += " AND id != $2"
            params.append(exclude_id)

        count = await conn.fetchval(query, *params)
        if count > 1:
            await conn.execute(
                """
                UPDATE sender_details 
                SET is_default = false 
                WHERE user_id = $1 
                AND id != (
                    SELECT id FROM sender_details 
                    WHERE user_id = $1 AND is_default = true 
                    ORDER BY created_at DESC LIMIT 1
                )
                """,
                user_id,
            )

    async def create_sender_detail(self, user_id: UUID, data: Dict) -> Dict:
        """Create a new sender detail"""
        try:
            async with db.pool.acquire() as conn:
                async with conn.transaction():
                    # Check existing records
                    existing_count = await conn.fetchval(
                        "SELECT COUNT(*) FROM sender_details WHERE user_id = $1",
                        user_id,
                    )

                    is_default = data.get("is_default", False) or existing_count == 0

                    # If setting as default, unset others
                    if is_default:
                        await conn.execute(
                            """
                            UPDATE sender_details
                            SET is_default = false
                            WHERE user_id = $1
                            """,
                            user_id,
                        )

                    # Create new sender detail
                    sender_detail = await conn.fetchrow(
                        """
                        INSERT INTO sender_details (
                            user_id, name, address, is_default
                        ) VALUES ($1, $2, $3, $4)
                        RETURNING *
                        """,
                        user_id,
                        data["name"],
                        data["address"],
                        is_default,
                    )

                    # Verify data consistency
                    await self._ensure_single_default(conn, user_id)

                    return dict(sender_detail)

        except Exception as e:
            logger.error(f"Error creating sender detail: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_sender_details(self, user_id: UUID) -> Dict:
        """Get all sender details for a user"""
        try:
            async with db.pool.acquire() as conn:
                # First ensure data consistency
                await self._ensure_single_default(conn, user_id)

                # Fetch sender details
                rows = await conn.fetch(
                    """
                    SELECT 
                        id,
                        user_id,
                        name,
                        address,
                        is_default,
                        created_at,
                        updated_at
                    FROM sender_details
                    WHERE user_id = $1
                    ORDER BY is_default DESC, created_at DESC
                    """,
                    user_id,
                )

                sender_details = [dict(row) for row in rows]

                return {
                    "count": len(sender_details),
                    "data": sender_details,
                    "message": (
                        "Sender details retrieved successfully"
                        if sender_details
                        else "No sender details found"
                    ),
                }

        except Exception as e:
            logger.error(f"Error fetching sender details: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_default_sender_detail(self, user_id: UUID) -> Dict:
        """Get the default sender detail for a user"""
        try:
            async with db.pool.acquire() as conn:
                # Ensure data consistency
                await self._ensure_single_default(conn, user_id)

                sender_detail = await conn.fetchrow(
                    """
                    SELECT 
                        id,
                        user_id,
                        name,
                        address,
                        is_default,
                        created_at,
                        updated_at
                    FROM sender_details
                    WHERE user_id = $1 AND is_default = true
                    """,
                    user_id,
                )

                if not sender_detail:
                    raise NotFoundError("No default sender detail found")

                return dict(sender_detail)

        except NotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(f"Error fetching default sender detail: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def update_sender_detail(self, id: UUID, user_id: UUID, data: Dict) -> Dict:
        """Update a sender detail"""
        try:
            async with db.pool.acquire() as conn:
                async with conn.transaction():
                    # Check if the sender detail exists
                    existing = await conn.fetchrow(
                        "SELECT is_default FROM sender_details WHERE id = $1 AND user_id = $2",
                        id,
                        user_id,
                    )

                    if not existing:
                        raise NotFoundError("Sender detail not found")

                    new_is_default = data.get("is_default")

                    # If setting as default
                    if new_is_default:
                        await conn.execute(
                            """
                            UPDATE sender_details
                            SET is_default = false
                            WHERE user_id = $1 AND id != $2
                            """,
                            user_id,
                            id,
                        )

                    # Update the sender detail
                    sender_detail = await conn.fetchrow(
                        """
                        UPDATE sender_details
                        SET name = $1,
                            address = $2,
                            is_default = COALESCE($3, is_default),
                            updated_at = NOW()
                        WHERE id = $4 AND user_id = $5
                        RETURNING *
                        """,
                        data["name"],
                        data["address"],
                        new_is_default,
                        id,
                        user_id,
                    )

                    # Verify data consistency
                    await self._ensure_single_default(conn, user_id)

                    return dict(sender_detail)

        except NotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(f"Error updating sender detail: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def delete_sender_detail(self, id: UUID, user_id: UUID) -> Dict:
        """Delete a sender detail"""
        try:
            async with db.pool.acquire() as conn:
                async with conn.transaction():
                    # Get current state
                    current_detail = await conn.fetchrow(
                        "SELECT is_default FROM sender_details WHERE id = $1 AND user_id = $2",
                        id,
                        user_id,
                    )

                    if not current_detail:
                        raise NotFoundError("Sender detail not found")

                    # If deleting default, set another as default if exists
                    if current_detail["is_default"]:
                        await conn.execute(
                            """
                            UPDATE sender_details 
                            SET is_default = true 
                            WHERE user_id = $1 AND id != $2
                            AND id = (
                                SELECT id FROM sender_details 
                                WHERE user_id = $1 AND id != $2
                                ORDER BY created_at ASC LIMIT 1
                            )
                            """,
                            user_id,
                            id,
                        )

                    # Delete the sender detail
                    await conn.execute("DELETE FROM sender_details WHERE id = $1", id)

                    return {"message": "Sender detail deleted successfully"}

        except NotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(f"Error deleting sender detail: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
