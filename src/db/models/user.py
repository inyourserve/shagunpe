from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    phone: str = Field(..., pattern=r"^\+?1?\d{9,15}$")


class UserResponse(BaseModel):
    id: str
    phone: str
    status: str
    balance: float = 0
    hold_balance: float = 0
