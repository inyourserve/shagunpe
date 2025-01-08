# src/core/config/app.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    APP_NAME: str = "ShagunPE"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    SECRET_KEY: str
    ENCRYPTION_KEY: str

    # Database
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str
    SSL_MODE: str = "require"  # Fixed field name

    # Redis
    REDIS_URL: str

    # MSG91
    MSG91_AUTH_KEY: str
    MSG91_TEMPLATE_ID: str

    class Config:
        env_file = ".env"


settings = Settings()
