# src/core/logging/logger.py
import logging
import json
from datetime import datetime
from typing import Any

from src.services.auth import phone


class CustomLogger:
    def __init__(self):
        self.logger = logging.getLogger("shagunpe")
        self.logger.setLevel(logging.INFO)

        # File Handler
        fh = logging.FileHandler("logs/shagunpe.log")
        fh.setFormatter(
            logging.Formatter(
                '{"timestamp":"%(asctime)s", "level":"%(levelname)s", "message":%(message)s}'
            )
        )
        self.logger.addHandler(fh)

    def log_event(self, event_type: str, data: dict[str, Any]):
        message = json.dumps({"event": event_type, "data": data})
        self.logger.info(message)


# Usage in auth service
logger = CustomLogger()
logger.log_event("otp_sent", {"phone": phone, "timestamp": datetime.utcnow()})
