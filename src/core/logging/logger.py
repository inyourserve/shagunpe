import logging
import os
from datetime import datetime

# Create logs directory
os.makedirs("logs", exist_ok=True)

# Create logger
logger = logging.getLogger("shagunpe")
logger.setLevel(logging.DEBUG)

# Create formatters and handlers
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)

# Console Handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# File Handler
file_handler = logging.FileHandler("logs/shagunpe.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
