# src/core/security/jwt.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer
from src.core.config.app import settings

security = HTTPBearer()


class JWTHandler:
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 60 * 24  # 24 hours

    def create_access_token(self, phone: str) -> str:
        data = {
            "phone": phone,
            "exp": datetime.utcnow()
            + timedelta(minutes=self.access_token_expire_minutes),
        }
        return jwt.encode(data, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> dict:
        try:
            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")


jwt_handler = JWTHandler()
