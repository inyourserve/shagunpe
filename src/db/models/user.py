# src/db/models/user.py
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    phone: str = Field(..., pattern=r"^\+?1?\d{9,15}$")


class UserResponse(BaseModel):
    phone: str
