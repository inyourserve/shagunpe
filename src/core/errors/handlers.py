# src/core/errors/handlers.py
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


async def auth_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": True, "message": exc.detail, "code": "AUTH_ERROR"},
    )
