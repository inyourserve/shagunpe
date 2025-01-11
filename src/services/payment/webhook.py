# src/services/payment/webhook.py
from fastapi import HTTPException
from typing import Dict, List
from src.core.config.database import db
import json
import logging
from datetime import datetime

logger = logging.getLogger("shagunpe")


class WebhookHandler:
    def __init__(self):
        self.status_mapping = {
            "payment.captured": "completed",
            "payment.failed": "failed",
            "payment.authorized": "processing",
            "order.paid": "completed",
        }

    async def handle_payment_webhook(self, body: bytes, signature: str) -> Dict:
        """Handle single webhook"""
        try:
            # Parse webhook data
            payload = json.loads(body)
            event = payload.get("event")

            # Extract payment details
            payment_entity = (
                payload.get("payload", {}).get("payment", {}).get("entity", {})
            )
            order_id = payment_entity.get("order_id")

            if not order_id:
                return {"status": "invalid_payload"}

            async with db.pool.acquire() as conn:
                async with conn.transaction():
                    # Quick check if payment exists
                    payment = await conn.fetchrow(
                        """
                        SELECT id, status 
                        FROM payments 
                        WHERE gateway_payment_id = $1
                        """,
                        order_id,
                    )

                    if not payment:
                        return {"status": "payment_not_found"}

                    # If already completed, skip processing
                    if payment["status"] == "completed":
                        return {"status": "already_processed"}

                    # Process the payment
                    new_status = self.status_mapping.get(event, "pending")
                    await self._update_payment_status(
                        conn, payment["id"], new_status, payload
                    )

                    return {"status": "success", "new_status": new_status}

        except json.JSONDecodeError:
            return {"status": "invalid_json"}
        except Exception as e:
            logger.error(f"Webhook processing failed: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def process_webhook_batch(self, webhooks: List[Dict]):
        """Process multiple webhooks in batch"""
        async with db.pool.acquire() as conn:
            async with conn.transaction():
                for webhook in webhooks:
                    try:
                        event = webhook.get("event")
                        payment_entity = (
                            webhook.get("payload", {})
                            .get("payment", {})
                            .get("entity", {})
                        )
                        order_id = payment_entity.get("order_id")

                        if not order_id:
                            continue

                        # Quick status check
                        payment = await conn.fetchrow(
                            "SELECT id, status FROM payments WHERE gateway_payment_id = $1",
                            order_id,
                        )

                        if not payment or payment["status"] == "completed":
                            continue

                        # Update status
                        new_status = self.status_mapping.get(event, "pending")
                        await self._update_payment_status(
                            conn, payment["id"], new_status, webhook
                        )

                    except Exception as e:
                        logger.error(f"Error processing webhook in batch: {str(e)}")
                        continue

    async def _update_payment_status(
        self, conn, payment_id: str, status: str, webhook_data: Dict
    ):
        """Update payment status efficiently"""
        if status == "completed":
            await conn.execute(
                """
                WITH payment_update AS (
                    UPDATE payments 
                    SET status = $1,
                        metadata = $2,
                        updated_at = NOW()
                    WHERE id = $3
                    RETURNING transaction_id
                )
                UPDATE transactions
                SET status = 'completed',
                    updated_at = NOW()
                WHERE id = (SELECT transaction_id FROM payment_update)
                """,
                status,
                json.dumps(webhook_data),
                payment_id,
            )
        else:
            await conn.execute(
                """
                UPDATE payments 
                SET status = $1,
                    metadata = $2,
                    updated_at = NOW()
                WHERE id = $3
                """,
                status,
                json.dumps(webhook_data),
                payment_id,
            )
