# /core/security/jwt.py
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import HTTPException, Depends
from jose import JWTError, jwt
from datetime import datetime, timedelta
from src.core.config.app import settings
from src.core.logging import logger

security = HTTPBearer()


class JWTHandler:
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 60 * 24  # 24 hours

    def create_access_token(self, data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})

        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            raise HTTPException(
                status_code=401, detail="Could not validate credentials"
            )

    async def get_current_user(
        self, credentials: HTTPAuthorizationCredentials = Depends(security)
    ):
        return self.verify_token(credentials.credentials)


jwt_handler = JWTHandler()
