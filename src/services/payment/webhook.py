# src/services/payment/webhook.py
from fastapi import HTTPException
from typing import Dict
from src.core.config.database import db
from src.cache.redis import redis_client  # Import Redis client
import json
import logging

logger = logging.getLogger("shagunpe")


# src/services/payment/webhook.py
class WebhookHandler:
    def __init__(self):
        # Map Razorpay events to our status types
        self.payment_status_mapping = {
            "payment.captured": "completed",
            "payment.failed": "failed",
            "payment.authorized": "processing",
            "order.paid": "completed",
        }

        # Separate mapping for transaction status
        self.transaction_status_mapping = {
            "payment.captured": "completed",
            "payment.failed": "failed",
            "payment.authorized": "pending",  # Keep as pending until captured
            "order.paid": "completed",
        }

    async def handle_payment_webhook(self, body: bytes, signature: str) -> Dict:
        try:
            payload = json.loads(body)
            event = payload.get("event")
            payment_entity = (
                payload.get("payload", {}).get("payment", {}).get("entity", {})
            )
            order_id = payment_entity.get("order_id")

            logger.info(f"Processing webhook: event={event}, order_id={order_id}")

            if not order_id:
                return {"status": "invalid_payload"}

            async with db.pool.acquire() as conn:
                async with conn.transaction():
                    payment = await conn.fetchrow(
                        """
                        SELECT p.*, t.event_id, t.amount as transaction_amount
                        FROM payments p
                        INNER JOIN transactions t ON p.transaction_id = t.id
                        WHERE p.gateway_payment_id = $1
                        FOR UPDATE
                        """,
                        order_id,
                    )

                    if not payment:
                        return {"status": "payment_not_found"}

                    # Get new statuses from event
                    new_payment_status = self.payment_status_mapping.get(event)
                    new_transaction_status = self.transaction_status_mapping.get(event)

                    if not new_payment_status:
                        return {"status": "unhandled_event"}

                    if new_payment_status == "completed":
                        await conn.execute(
                            """
                            WITH payment_update AS (
                                UPDATE payments 
                                SET status = $1::payment_status,
                                    gateway_response = $2,
                                    updated_at = NOW()
                                WHERE id = $3
                                RETURNING transaction_id
                            ), transaction_update AS (
                                UPDATE transactions
                                SET status = $4::transaction_status,
                                    updated_at = NOW()
                                WHERE id = (SELECT transaction_id FROM payment_update)
                                RETURNING event_id
                            )
                            UPDATE events
                            SET total_amount = total_amount + $5,
                                online_amount = online_amount + $5,
                                updated_at = NOW()
                            WHERE id = (SELECT event_id FROM transaction_update)
                            """,
                            new_payment_status,
                            json.dumps(payload),
                            payment["id"],
                            new_transaction_status,
                            payment["transaction_amount"],
                        )
                    else:
                        # Update statuses for other events
                        await conn.execute(
                            """
                            WITH payment_update AS (
                                UPDATE payments 
                                SET status = $1::payment_status,
                                    gateway_response = $2,
                                    updated_at = NOW()
                                WHERE id = $3
                            )
                            UPDATE transactions
                            SET status = $4::transaction_status,
                                updated_at = NOW()
                            WHERE id = $5
                            """,
                            new_payment_status,
                            json.dumps(payload),
                            payment["id"],
                            new_transaction_status,
                            payment["transaction_id"],
                        )

                    return {
                        "status": "success",
                        "payment_status": new_payment_status,
                        "transaction_status": new_transaction_status,
                        "order_id": order_id,
                    }

        except Exception as e:
            logger.error(f"Webhook processing failed: {str(e)}")
            return {"status": "error", "message": str(e)}
