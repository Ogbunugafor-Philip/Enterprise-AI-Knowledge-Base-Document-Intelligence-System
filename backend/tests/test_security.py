import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.responses import PlainTextResponse
from starlette.requests import Request

from app.core import cors_config, secret_protection
from app.core.rate_limiter import RateLimiter
from app.middleware.security_middleware import SQLInjectionProtectionMiddleware, SecurityHeadersMiddleware
from app.services import security_scan_service


def _request(path="/items", query_string=b""):
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": path,
            "query_string": query_string,
            "headers": [],
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 80),
            "scheme": "http",
        }
    )


async def _call_next(request):
    return PlainTextResponse("ok")


def test_security_headers_middleware_adds_content_type_options_header():
    middleware = SecurityHeadersMiddleware(app=None)
    response = asyncio.run(middleware.dispatch(_request(), _call_next))

    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_security_headers_middleware_adds_frame_options_header():
    middleware = SecurityHeadersMiddleware(app=None)
    response = asyncio.run(middleware.dispatch(_request(), _call_next))

    assert response.headers["X-Frame-Options"] == "DENY"


def test_sql_injection_protection_middleware_detects_union_select_pattern():
    middleware = SQLInjectionProtectionMiddleware(app=None)
    response = asyncio.run(middleware.dispatch(_request("/search", b"q=UNION%20SELECT%20password"), _call_next))

    assert response.status_code == 400


def test_sql_injection_protection_middleware_detects_or_1_equals_1_pattern():
    middleware = SQLInjectionProtectionMiddleware(app=None)
    response = asyncio.run(middleware.dispatch(_request("/search", b"q=OR%201=1"), _call_next))

    assert response.status_code == 400


def test_sql_injection_protection_middleware_allows_clean_requests_through():
    middleware = SQLInjectionProtectionMiddleware(app=None)
    response = asyncio.run(middleware.dispatch(_request("/search", b"q=policy"), _call_next))

    assert response.status_code == 200
    assert response.body == b"ok"


def test_rate_limiter_rate_limit_login_blocks_after_10_attempts():
    limiter = RateLimiter()
    for _ in range(10):
        limiter.rate_limit_login("127.0.0.1", email=None)

    with pytest.raises(HTTPException) as exc:
        limiter.rate_limit_login("127.0.0.1", email=None)

    assert exc.value.status_code == 429


def test_cors_config_get_cors_origins_never_returns_wildcard_in_production_mode(monkeypatch):
    monkeypatch.setattr(cors_config, "settings", SimpleNamespace(FRONTEND_URL="https://app.example.com", ENVIRONMENT="production"))

    assert "*" not in cors_config.get_cors_origins()


def test_cors_config_get_cors_origins_returns_configured_frontend_url(monkeypatch):
    monkeypatch.setattr(cors_config, "settings", SimpleNamespace(FRONTEND_URL="https://app.example.com", ENVIRONMENT="production"))

    assert "https://app.example.com" in cors_config.get_cors_origins()


def test_secret_protection_sanitize_log_entry_removes_password_field():
    sanitized = secret_protection.sanitize_log_entry({"password": "Secret1!", "email": "user@example.com"})

    assert sanitized["password"] == "REDACTED"


def test_secret_protection_sanitize_log_entry_removes_otp_code_field():
    sanitized = secret_protection.sanitize_log_entry({"otp_code": "123456"})

    assert sanitized["otp_code"] == "REDACTED"


def test_security_scan_service_run_security_checklist_returns_security_checklist_report():
    report = asyncio.run(security_scan_service.run_security_checklist())

    assert report.checks
    assert report.overall_status in {"PASS", "FAIL"}
    assert hasattr(report, "critical_failures")


def test_validate_environment_secrets_flags_weak_jwt_secret(monkeypatch):
    weak_settings = SimpleNamespace(
        JWT_SECRET_KEY="short",
        ENCRYPTION_KEY="long-enough-development-encryption-key",
        CEREBRAS_API_KEY="realistic-key",
        POSTGRES_PASSWORD="realistic-password",
        SMTP_PASSWORD="realistic-password",
    )
    import app.core.config as config

    monkeypatch.setattr(config, "settings", weak_settings)
    warnings = secret_protection.validate_environment_secrets()

    assert any("JWT_SECRET_KEY" in warning for warning in warnings)
