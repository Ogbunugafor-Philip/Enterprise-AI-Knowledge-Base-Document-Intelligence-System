import re
from collections.abc import Mapping
from typing import Any

SENSITIVE_FIELDS = {"password", "hashed_password", "otp_code", "api_key", "secret_key", "token"}
SECRET_PATTERNS = (
    re.compile(r"Bearer\s+[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+"),
    re.compile(r"(?i)(api[_-]?key|secret[_-]?key|password)\s*[:=]\s*['\"]?[^,'\"\s}]+"),
    re.compile(r"eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+"),
)


def scan_for_exposed_secrets(value: Any) -> Any:
    if isinstance(value, str):
        redacted = value
        for pattern in SECRET_PATTERNS:
            redacted = pattern.sub("REDACTED", redacted)
        return redacted
    if isinstance(value, Mapping):
        return sanitize_log_entry(dict(value))
    if isinstance(value, list):
        return [scan_for_exposed_secrets(item) for item in value]
    return value


def sanitize_log_entry(entry: dict) -> dict:
    sanitized = {}
    for key, value in entry.items():
        if key.lower() in SENSITIVE_FIELDS or any(field in key.lower() for field in SENSITIVE_FIELDS):
            sanitized[key] = "REDACTED"
        else:
            sanitized[key] = scan_for_exposed_secrets(value)
    return sanitized


def validate_environment_secrets() -> list[str]:
    warnings: list[str] = []
    try:
        from app.core.config import settings
    except Exception as exc:
        return [f"Settings could not be loaded: {exc}"]

    required = {
        "JWT_SECRET_KEY": settings.JWT_SECRET_KEY,
        "ENCRYPTION_KEY": settings.ENCRYPTION_KEY,
        "CEREBRAS_API_KEY": settings.CEREBRAS_API_KEY,
        "POSTGRES_PASSWORD": settings.POSTGRES_PASSWORD,
        "SMTP_PASSWORD": settings.SMTP_PASSWORD,
    }
    placeholders = {"changeme", "change-me", "placeholder", "secret", "password", "test", "dev"}
    for name, value in required.items():
        if not value:
            warnings.append(f"{name} is not set")
        elif str(value).strip().lower() in placeholders or "placeholder" in str(value).lower():
            warnings.append(f"{name} appears to be a placeholder")
    if len(settings.JWT_SECRET_KEY or "") < 32:
        warnings.append("JWT_SECRET_KEY must be at least 32 characters")
    if len(settings.ENCRYPTION_KEY or "") < 32:
        warnings.append("ENCRYPTION_KEY should be at least 32 characters")
    return warnings
