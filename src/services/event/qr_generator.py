# services/event/qr_generator.py
import qrcode
from PIL import Image
import io
import base64
import os
import logging
from src.core.config.database import db

logger = logging.getLogger("shagunpe")


class EventQRGenerator:
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        src_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        self.logo_path = os.path.join(src_dir, "src", "assets", "logo.png")

    async def generate_and_store(self, event_data: dict):
        """Generate QR code and store it"""
        try:
            qr_code = await self._generate_qr(event_data)
            await self._store_qr(event_data["id"], qr_code)
            return qr_code
        except Exception as e:
            logger.error(f"Error in QR generation: {str(e)}")
            raise

    async def get_qr(self, event_id: str, force_refresh: bool = False):
        """Get QR code from storage or generate new"""
        try:
            if not force_refresh:
                qr_code = await self._get_stored_qr(event_id)
                if qr_code:
                    return qr_code

            async with db.pool.acquire() as conn:
                event = await conn.fetchrow(
                    "SELECT * FROM events WHERE id = $1", event_id
                )
                if not event:
                    raise ValueError("Event not found")

                return await self.generate_and_store(dict(event))

        except Exception as e:
            logger.error(f"Error getting QR: {str(e)}")
            raise

    async def _generate_qr(self, event_data: dict) -> str:
        """Generate QR code with logo"""
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )

        qr_data = {
            "event_id": str(event_data["id"]),
            "shagun_id": event_data["shagun_id"],
            "type": "shagunpe_event",
        }
        qr.add_data(qr_data)
        qr.make(fit=True)

        qr_image = qr.make_image(fill_color="black", back_color="white").convert("RGBA")

        # Add logo if exists
        if os.path.exists(self.logo_path):
            logo = Image.open(self.logo_path)
            logo_size = qr_image.size[0] // 4
            logo = logo.resize((logo_size, logo_size))

            pos = (
                (qr_image.size[0] - logo.size[0]) // 2,
                (qr_image.size[1] - logo.size[1]) // 2,
            )

            logo_bg = Image.new("RGBA", logo.size, "white")
            qr_image.paste(logo_bg, pos, logo_bg)
            qr_image.paste(logo, pos, logo)

        buffered = io.BytesIO()
        qr_image.save(buffered, format="PNG", optimize=True, quality=85)
        return f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode()}"

    async def _store_qr(self, event_id: str, qr_code: str):
        """Store QR in database"""
        async with db.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE events 
                SET qr_code = $1, 
                    qr_code_updated_at = NOW()
                WHERE id = $2
                """,
                qr_code,
                event_id,
            )

    async def _get_stored_qr(self, event_id: str) -> str:
        """Get stored QR code"""
        async with db.pool.acquire() as conn:
            result = await conn.fetchrow(
                "SELECT qr_code FROM events WHERE id = $1", event_id
            )
            return result["qr_code"] if result else None
