# src/services/payment/gateway/base.py
from abc import ABC, abstractmethod
from typing import Dict


class PaymentGateway(ABC):
    @abstractmethod
    async def initialize_payment(
        self, amount: float, transaction_id: str, metadata: Dict
    ) -> Dict:
        pass

    @abstractmethod
    async def verify_payment(self, payment_id: str) -> Dict:
        pass

    @abstractmethod
    async def process_webhook(self, payload: Dict) -> Dict:
        pass
