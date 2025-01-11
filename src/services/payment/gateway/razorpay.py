# src/services/payment/gateway/razorpay.py
import razorpay
from src.core.errors.payment import PaymentError, PaymentGatewayError
from src.core.config.app import settings
from typing import Dict
import logging

logger = logging.getLogger("shagunpe")


class RazorpayGateway:
    def __init__(self):
        try:
            # Initialize Razorpay client with your credentials
            self.client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )
            logger.info("Initialized Razorpay gateway")
        except Exception as e:
            logger.error(f"Failed to initialize Razorpay client: {str(e)}")
            raise PaymentGatewayError("Payment gateway initialization failed")

    async def create_payment(
        self, amount: float, transaction_id: str, metadata: Dict
    ) -> Dict:
        """
        Creates a Razorpay order
        Returns order details needed for frontend integration
        """
        try:
            data = {
                "amount": int(amount * 100),  # Convert to paise
                "currency": "INR",
                "receipt": str(transaction_id),
                "notes": metadata,
                "payment_capture": 1,  # Auto capture payment
            }

            order = self.client.order.create(data=data)

            # Return data needed for frontend integration
            return {
                "gateway_payment_id": order["id"],  # This is the order_id
                "amount": amount,
                "currency": "INR",
                "status": order["status"],
                "key": settings.RAZORPAY_KEY_ID,  # Frontend needs this
                "order_id": order["id"],
                "prefill": {
                    "name": metadata.get("sender_name", ""),
                    "contact": metadata.get("contact", ""),
                },
            }

        except Exception as e:
            logger.error(f"Payment creation failed: {str(e)}")
            raise PaymentError("Failed to create payment")

    async def verify_signature(self, payment_data: Dict) -> bool:
        """
        Verifies Razorpay payment signature
        Called when payment is completed
        """
        try:
            # Verify signature
            params_dict = {
                "razorpay_order_id": payment_data["razorpay_order_id"],
                "razorpay_payment_id": payment_data["razorpay_payment_id"],
                "razorpay_signature": payment_data["razorpay_signature"],
            }
            return self.client.utility.verify_payment_signature(params_dict)

        except Exception as e:
            logger.error(f"Payment signature verification failed: {str(e)}")
            return False

    async def get_payment_details(self, payment_id: str) -> Dict:
        """
        Fetch payment details from Razorpay
        """
        try:
            payment = self.client.payment.fetch(payment_id)
            return payment
        except Exception as e:
            logger.error(f"Failed to fetch payment details: {str(e)}")
            raise PaymentError("Failed to fetch payment details")
