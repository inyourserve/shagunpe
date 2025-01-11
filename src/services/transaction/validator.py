# src/services/transaction/validator.py
from fastapi import HTTPException
from typing import Dict
from decimal import Decimal


class TransactionValidator:
    @staticmethod
    def validate_transaction_create(data: Dict) -> None:
        """Validate transaction creation data"""
        if not data.get("amount"):
            raise HTTPException(status_code=400, detail="Amount is required")

        if Decimal(str(data["amount"])) <= 0:
            raise HTTPException(status_code=400, detail="Amount must be greater than 0")

        if data.get("type") not in ["online", "cash"]:
            raise HTTPException(status_code=400, detail="Invalid transaction type")

        if data["type"] == "cash" and not data.get("sender_name"):
            raise HTTPException(
                status_code=400, detail="Sender name is required for cash transactions"
            )

    @staticmethod
    def validate_transaction_access(transaction: Dict, user_id: str) -> None:
        """Validate user access to transaction"""
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")

        if str(transaction["sender_id"]) != str(user_id) and str(
            transaction["receiver_id"]
        ) != str(user_id):
            raise HTTPException(
                status_code=403, detail="Not authorized to access this transaction"
            )
