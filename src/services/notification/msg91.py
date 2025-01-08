# src/services/notification/msg91.py
import httpx
from src.core.config.app import settings


class MSG91Client:
    def __init__(self):
        self.template_id = settings.MSG91_TEMPLATE_ID
        self.auth_key = settings.MSG91_AUTH_KEY
        self.base_url = "https://control.msg91.com/api/v5"

    async def send_otp(self, phone: str) -> bool:
        url = f"{self.base_url}/otp"
        params = {
            "template_id": self.template_id,
            "mobile": phone,
            "authkey": self.auth_key,
        }

        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(url, params=params)
            return response.status_code == 200 and '"type":"success"' in response.text

    async def verify_otp(self, phone: str, otp: str) -> bool:
        url = f"{self.base_url}/otp/verify"
        params = {"mobile": phone, "otp": otp, "authkey": self.auth_key}

        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(url, params=params)
            return response.status_code == 200 and '"type":"success"' in response.text
