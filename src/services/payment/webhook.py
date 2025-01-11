# src/services/payment/webhook.py
from fastapi import HTTPException
from typing import Dict
from src.core.config.database import db
import logging
import json

logger = logging.getLogger("shagunpe")


class WebhookHandler:

    # In WebhookHandler:
    async def handle_payment_webhook(self, payload: Dict, signature: str) -> Dict:
        try:
            # Verify webhook signature first
            if not self.verify_webhook_signature(payload, signature):
                logger.error("Invalid webhook signature")
                return {"status": "invalid_signature"}

            async with db.pool.acquire() as conn:
                async with conn.transaction():
                    # Get payment with transaction details
                    payment = await conn.fetchrow(
                        """
                        SELECT p.*, t.event_id, t.amount
                        FROM payments p
                        INNER JOIN transactions t ON p.transaction_id = t.id
                        WHERE p.gateway_payment_id = $1
                        FOR UPDATE
                        """,
                        payload["payload"]["payment"]["entity"]["order_id"],
                    )

                    if not payment:
                        logger.error("Payment not found for webhook")
                        return {"status": "ignored"}

                    # Prevent duplicate webhook processing
                    if payment["status"] == "completed":
                        return {"status": "already_processed"}

                    status = self._map_gateway_status(payload["event"])

                    # Update all related records atomically
                    if status == "completed":
                        await conn.execute(
                            """
                            WITH payment_update AS (
                                UPDATE payments 
                                SET status = $1,
                                    metadata = $2,
                                    updated_at = NOW()
                                WHERE id = $3
                            ), transaction_update AS (
                                UPDATE transactions
                                SET status = 'completed',
                                    updated_at = NOW()
                                WHERE id = $4
                            )
                            UPDATE events
                            SET total_amount = total_amount + $5,
                                online_amount = online_amount + $5,
                                updated_at = NOW()
                            WHERE id = $6
                            """,
                            status,
                            json.dumps(payload),
                            payment["id"],
                            payment["transaction_id"],
                            payment["amount"],
                            payment["event_id"],
                        )
                    else:
                        # Just update payment and transaction status
                        await conn.execute(
                            """
                            WITH payment_update AS (
                                UPDATE payments 
                                SET status = $1,
                                    metadata = $2,
                                    updated_at = NOW()
                                WHERE id = $3
                            )
                            UPDATE transactions
                            SET status = $1,
                                updated_at = NOW()
                            WHERE id = $4
                            """,
                            status,
                            json.dumps(payload),
                            payment["id"],
                            payment["transaction_id"],
                        )

                    return {"status": "processed"}

        except Exception as e:
            logger.error(f"Webhook processing failed: {str(e)}")
            # Still return 200 to avoid webhook retries
            return {"status": "error", "message": str(e)}

    def _map_gateway_status(self, event: str) -> str:
        status_mapping = {
            "payment.captured": "completed",
            "payment.failed": "failed",
            "payment.pending": "pending",
        }
        return status_mapping.get(event, "unknown")
