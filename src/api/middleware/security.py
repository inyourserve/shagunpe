# src/api/middleware/security.py
from fastapi import Request, HTTPException
import ipaddress


async def security_middleware(request: Request, call_next):
    client_ip = request.client.host

    # Check if IP is private
    if ipaddress.ip_address(client_ip).is_private:
        raise HTTPException(status_code=403)

    # Check request headers
    headers = request.headers
    if headers.get("user-agent", "").lower().startswith("curl"):
        raise HTTPException(status_code=403)

    response = await call_next(request)

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"

    return response
