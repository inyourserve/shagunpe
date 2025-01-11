# services/event/event_processor.py
import logging
from src.services.event.qr_generator import EventQRGenerator

logger = logging.getLogger("shagunpe")


class EventProcessor:
    def __init__(self):
        self.qr_generator = EventQRGenerator()

    async def process_new_event(self, event_data: dict):
        """Process new event creation tasks"""
        try:
            # Generate QR code
            await self.qr_generator.generate_and_store(event_data)

            # Future tasks:
            # - Send notifications
            # - Update statistics
            # - Process event analytics

        except Exception as e:
            logger.error(f"Error processing event {event_data['id']}: {str(e)}")

    async def process_event_update(self, event_data: dict):
        """Process event update tasks"""
        try:
            # Regenerate QR if needed
            await self.qr_generator.generate_and_store(event_data)

        except Exception as e:
            logger.error(f"Error processing event update {event_data['id']}: {str(e)}")
