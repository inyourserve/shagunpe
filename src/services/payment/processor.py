# src/services/payment/processor.py
from typing import Dict
from .gateway.razorpay import RazorpayGateway
from src.core.config.database import db
from src.core.errors.payment import PaymentError, PaymentGatewayError
from src.core.config.app import settings
import logging
import json

logger = logging.getLogger("shagunpe")


class PaymentProcessor:
    def __init__(self):
        try:
            self.gateway = RazorpayGateway()
            self.is_test_mode = getattr(settings, "PAYMENT_TEST_MODE", True)
            logger.info(
                f"Initialized PaymentProcessor in {'test' if self.is_test_mode else 'live'} mode"
            )
        except Exception as e:
            logger.error(f"Failed to initialize payment processor: {str(e)}")
            raise PaymentGatewayError("Payment system initialization failed")

    async def process_payment(self, transaction_id: str, payment_data: Dict) -> Dict:
        try:
            async with db.pool.acquire() as conn:
                # Get transaction
                transaction = await conn.fetchrow(
                    "SELECT * FROM transactions WHERE id = $1", transaction_id
                )

                if not transaction:
                    raise PaymentError("Transaction not found")

                # Create payment in gateway
                gateway_response = await self.gateway.create_payment(
                    amount=float(transaction["amount"]),
                    transaction_id=str(transaction["id"]),
                    metadata=payment_data.get("metadata", {}),
                )

                # Convert dictionary to JSON string for JSONB columns
                metadata = json.dumps(gateway_response)

                # Store payment record
                payment = await conn.fetchrow(
                    """
                    INSERT INTO payments (
                        transaction_id,
                        amount,
                        payment_method,
                        gateway_payment_id,
                        status,
                        gateway_response,
                        metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING *
                    """,
                    transaction_id,
                    transaction["amount"],
                    payment_data["payment_method"],
                    gateway_response["gateway_payment_id"],
                    "initiated",
                    json.dumps(gateway_response),  # Convert to JSON string
                    metadata,
                )

                # Update transaction with payment reference
                await conn.execute(
                    """
                    UPDATE transactions 
                    SET upi_ref = $1, 
                        updated_at = NOW() 
                    WHERE id = $2
                    """,
                    gateway_response["gateway_payment_id"],
                    transaction_id,
                )

                return dict(payment)

        except Exception as e:
            logger.error(f"Payment processing failed: {str(e)}")
            raise PaymentError(str(e))

    # In PaymentProcessor.verify_payment:
    async def verify_payment(self, payment_id: str, verification_data: Dict) -> Dict:
        try:
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
                        payment_id,
                    )

                    if not payment:
                        raise PaymentError("Payment not found")

                    # Verify signature and amount match
                    is_valid = await self.gateway.verify_signature(verification_data)
                    if not is_valid:
                        raise PaymentError("Invalid payment signature")

                    # Update payment status
                    updated_payment = await conn.fetchrow(
                        """
                        UPDATE payments 
                        SET status = $1,
                            gateway_response = $2,
                            updated_at = NOW()
                        WHERE id = $3
                        RETURNING *
                        """,
                        "completed",
                        json.dumps(verification_data),
                        payment["id"],
                    )

                    # Update transaction and event amounts atomically
                    await conn.execute(
                        """
                        WITH transaction_update AS (
                            UPDATE transactions 
                            SET status = 'completed',
                                updated_at = NOW()
                            WHERE id = $1
                        )
                        UPDATE events
                        SET total_amount = total_amount + $2,
                            online_amount = online_amount + $2,
                            updated_at = NOW()
                        WHERE id = $3
                        """,
                        payment["transaction_id"],
                        payment["transaction_amount"],
                        payment["event_id"],
                    )

                    return dict(updated_payment)

        except Exception as e:
            logger.error(f"Payment verification failed: {str(e)}")
            raise PaymentError(str(e))
