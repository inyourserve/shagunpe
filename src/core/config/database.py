# src/core/config/database.py
from asyncpg import create_pool
import ssl

from src.core.config.app import settings


class Database:
    def __init__(self):
        self._pool = None

    async def initialize(self):
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            self._pool = await create_pool(
                user=settings.DB_USER,
                password=settings.DB_PASS,
                database=settings.DB_NAME,
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                ssl=ctx,
                command_timeout=60,
                min_size=2,
                max_size=10,
            )
            print("Database connected successfully!")
        except Exception as e:
            print(f"Failed to connect to database: {str(e)}")
            raise

    async def dispose(self):
        if self._pool:
            await self._pool.close()

    @property
    def pool(self):
        return self._pool


db = Database()
