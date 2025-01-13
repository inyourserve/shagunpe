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
            payment_entity = (
                payload.get("payload", {}).get("payment", {}).get("entity", {})
            )
            order_id = payment_entity.get("order_id")
            amount = payment_entity.get("amount")  # Amount in paise

            if not order_id:
                logger.error("No order_id in webhook")
                return {"status": "invalid_payload"}

            async with db.pool.acquire() as conn:
                async with conn.transaction():
                    # Get payment with transaction and event info
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
                        logger.error(f"Payment not found for order_id: {order_id}")
                        return {"status": "payment_not_found"}

                    # If payment already completed, skip processing
                    if payment["status"] == "completed":
                        return {"status": "already_processed"}

                    # Get new status from event
                    new_status = self.status_mapping.get(event, "pending")
                    logger.info(
                        f"Processing webhook: order_id={order_id}, event={event}, new_status={new_status}"
                    )

                    if new_status == "completed":
                        # Update payment, transaction and event
                        await conn.execute(
                            """
                            WITH payment_update AS (
                                UPDATE payments 
                                SET status = $1,
                                    metadata = $2,
                                    updated_at = NOW()
                                WHERE id = $3
                                RETURNING transaction_id
                            ), transaction_update AS (
                                UPDATE transactions
                                SET status = 'completed',
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
                            json.dumps(payload),  # Changed from webhook_data to payload
                            payment["id"],
                            payment["transaction_amount"],
                        )
                        logger.info(
                            f"Payment completed: order_id={order_id}, amount={payment['transaction_amount']}"
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
                            new_status,
                            json.dumps(payload),
                            payment["id"],
                            payment["transaction_id"],
                        )
                        logger.info(
                            f"Payment status updated: order_id={order_id}, status={new_status}"
                        )

                    return {
                        "status": "success",
                        "new_status": new_status,
                        "order_id": order_id,
                        "amount": amount,
                    }

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in webhook: {str(e)}")
            return {"status": "invalid_json"}
        except Exception as e:
            logger.error(f"Webhook processing failed: {str(e)}")
            return {"status": "error", "message": str(e)}
