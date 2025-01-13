# src/services/payment/webhook.py
from fastapi import HTTPException
from typing import Dict
from src.core.config.database import db
from src.cache.redis import redis_client  # Import Redis client
import json
import logging

logger = logging.getLogger("shagunpe")


class WebhookHandler:
    def __init__(self):
        self.status_mapping = {
            "payment.captured": "completed",
            "payment.failed": "failed",
            "payment.authorized": "processing",
            "order.paid": "completed"
        }

    async def is_duplicate_webhook(self, signature: str) -> bool:
        """Check if webhook was already processed"""
        key = f"webhook:processed:{signature}"
        return await redis_client.exists(key)

    async def mark_webhook_processed(self, signature: str):
        """Mark webhook as processed"""
        key = f"webhook:processed:{signature}"
        await redis_client.set(key, "1", expire=86400)  # 24 hours expiry

    async def handle_payment_webhook(self, body: bytes, signature: str) -> Dict:
        """Handle single webhook"""
        try:
            # Parse webhook data
            payload = json.loads(body)
            event = payload.get("event")
            payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
            order_id = payment_entity.get("order_id")

            logger.info(f"Processing webhook: event={event}, order_id={order_id}")

            # Check for duplicate webhook
            if await self.is_duplicate_webhook(signature):
                logger.info(f"Duplicate webhook received for order_id: {order_id}")
                return {"status": "already_processed"}

            async with db.pool.acquire() as conn:
                async with conn.transaction():
                    # Get payment with transaction info
                    payment = await conn.fetchrow(
                        """
                        SELECT p.*, t.event_id, t.amount as transaction_amount
                        FROM payments p
                        INNER JOIN transactions t ON p.transaction_id = t.id
                        WHERE p.gateway_payment_id = $1
                        FOR UPDATE
                        """,
                        order_id
                    )

                    if not payment:
                        logger.error(f"Payment not found for order_id: {order_id}")
                        return {"status": "payment_not_found"}

                    # Check if already completed
                    if payment['status'] == 'completed':
                        return {"status": "already_completed"}

                    # Get new status from event
                    new_status = self.status_mapping.get(event)
                    if not new_status:
                        return {"status": "unhandled_event"}

                    if new_status == "completed":
                        # Update payment, transaction and event amounts
                        await conn.execute(
                            """
                            WITH payment_update AS (
                                UPDATE payments 
                                SET status = $1,
                                    gateway_response = $2,
                                    updated_at = NOW()
                                WHERE id = $3
                                RETURNING transaction_id
                            ), transaction_update AS (
                                UPDATE transactions
                                SET status = $1,
                                    updated_at = NOW()
                                WHERE id = (SELECT transaction_id FROM payment_update)
                                RETURNING event_id
                            )
                            UPDATE events
                            SET total_amount = total_amount + $4,
                                online_amount = online_amount + $4,
                                updated_at = NOW()
                            WHERE id = (SELECT event_id FROM transaction_update)
                            """,
                            new_status,
                            json.dumps(payload),
                            payment['id'],
                            payment['transaction_amount']
                        )

                        # Mark webhook as processed in Redis
                        await self.mark_webhook_processed(signature)

                        logger.info(f"Payment completed for order_id: {order_id}")

                    else:
                        # Update failed/pending status
                        await conn.execute(
                            """
                            WITH payment_update AS (
                                UPDATE payments 
                                SET status = $1,
                                    gateway_response = $2,
                                    updated_at = NOW()
                                WHERE id = $3
                            )
                            UPDATE transactions
                            SET status = $1,
                                updated_at = NOW()
                            WHERE id = $4
                            """,
                            new_status,
                            json.dumps(payload),
                            payment['id'],
                            payment['transaction_id']
                        )

                        logger.info(f"Payment status updated to {new_status} for order_id: {order_id}")

                    return {
                        "status": "success",
                        "new_status": new_status,
                        "order_id": order_id
                    }

        except Exception as e:
            logger.error(f"Webhook processing failed: {str(e)}")
            return {"status": "error", "message": str(e)}

