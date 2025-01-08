import secrets
import base64

# Generate SECRET_KEY
secret_key = secrets.token_urlsafe(32)
print(f"SECRET_KEY={secret_key}")

# Generate ENCRYPTION_KEY
encryption_key = base64.b64encode(secrets.token_bytes(32)).decode()
print(f"ENCRYPTION_KEY={encryption_key}")
