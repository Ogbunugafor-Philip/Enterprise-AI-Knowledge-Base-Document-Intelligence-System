from app.core.config import settings


def get_cors_origins() -> list[str]:
    frontend_url = settings.FRONTEND_URL
    environment = (settings.ENVIRONMENT or "development").lower()
    origins = [frontend_url]
    if environment != "production":
        origins.extend([
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ])
    return [origin for origin in dict.fromkeys(origins) if origin and origin != "*"]


def get_cors_settings() -> dict:
    return {
        "allow_origins": get_cors_origins(),
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Authorization", "Content-Type", "X-Request-ID"],
        "max_age": 3600,
    }
