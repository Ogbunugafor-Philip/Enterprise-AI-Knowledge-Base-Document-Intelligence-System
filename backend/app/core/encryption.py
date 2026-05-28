import base64
import hashlib
import hmac
import secrets
from typing import Any

from cryptography.fernet import Fernet, InvalidToken


def _settings_key() -> str:
    try:
        from app.core.config import settings

        return settings.ENCRYPTION_KEY
    except Exception:
        return "development-test-encryption-key"


def _fernet() -> Fernet:
    digest = hashlib.sha256(_settings_key().encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_field(value: str | None) -> str | None:
    if value is None:
        return None
    return _fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_field(value: str | None) -> str | None:
    if value is None:
        return None
    try:
        return _fernet().decrypt(value.encode("utf-8")).decode("utf-8")
    except (InvalidToken, ValueError):
        return None


def encrypt_dict(data: dict[str, Any], fields: list[str] | tuple[str, ...]) -> dict[str, Any]:
    encrypted = dict(data)
    for field in fields:
        if field in encrypted and encrypted[field] is not None:
            encrypted[field] = encrypt_field(str(encrypted[field]))
    return encrypted


def hash_sensitive_data(value: str, salt: str | None = None) -> str:
    salt_value = salt or _settings_key()
    digest = hmac.new(salt_value.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"sha256:{digest}"


def generate_secure_token(num_bytes: int = 32) -> str:
    return secrets.token_urlsafe(num_bytes)
