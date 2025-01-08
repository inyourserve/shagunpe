# src/core/security/encryption.py
from cryptography.fernet import Fernet
from src.core.config.app import Settings


class Encryptor:
    def __init__(self):
        self.fernet = Fernet(Settings.ENCRYPTION_KEY)

    def encrypt_phone(self, phone: str) -> str:
        return self.fernet.encrypt(phone.encode()).decode()

    def decrypt_phone(self, encrypted_phone: str) -> str:
        return self.fernet.decrypt(encrypted_phone.encode()).decode()
