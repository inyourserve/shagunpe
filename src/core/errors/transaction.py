# src/core/errors/transaction.py
from fastapi import HTTPException, status


class TransactionError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class TransactionNotFoundError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
        )


class InvalidTransactionStateError(HTTPException):
    def __init__(self, state: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid transaction state: {state}",
        )
