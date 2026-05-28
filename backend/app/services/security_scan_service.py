from datetime import datetime, timezone
from pathlib import Path

from app.core.cors_config import get_cors_origins
from app.core.secret_protection import validate_environment_secrets
from app.schemas.security import SecurityCheckItem, SecurityChecklistReport


def _item(name: str, passed: bool, severity: str, description: str, recommendation: str) -> SecurityCheckItem:
    return SecurityCheckItem(
        check_name=name,
        status="PASS" if passed else "FAIL",
        severity=severity,
        description=description,
        recommendation=recommendation,
    )


def _file_contains(path: str, text: str) -> bool:
    try:
        return text in Path(path).read_text()
    except Exception:
        return False


async def run_security_checklist() -> SecurityChecklistReport:
    warnings = validate_environment_secrets()
    cors_origins = get_cors_origins()
    main_text = Path("backend/app/main.py").read_text() if Path("backend/app/main.py").exists() else ""
    nginx_text = Path("deployment/nginx/nginx.conf").read_text() if Path("deployment/nginx/nginx.conf").exists() else ""

    checks = [
        _item("Authentication middleware active", "JWTAuthenticationMiddleware" in main_text, "critical", "JWT authentication middleware is registered.", "Register JWTAuthenticationMiddleware in app startup."),
        _item("CORS restricted to approved domains", "*" not in cors_origins, "high", "CORS origins do not include wildcard.", "Remove wildcard origins in production."),
        _item("Rate limiting active on login endpoint", "RateLimitMiddleware" in main_text, "critical", "RateLimitMiddleware is registered.", "Enable login rate limiting middleware."),
        _item("SQL injection protection active", "SQLInjectionProtectionMiddleware" in main_text, "high", "SQL injection middleware is registered.", "Register SQLInjectionProtectionMiddleware."),
        _item("File upload malware scanning active", _file_contains("backend/app/workers/document_tasks.py", "malware_scan_service"), "high", "Document worker invokes malware scanning.", "Ensure uploaded files are scanned before processing."),
        _item("Security headers configured", "SecurityHeadersMiddleware" in main_text, "high", "Security headers middleware is registered.", "Register SecurityHeadersMiddleware."),
        _item("Environment secrets not placeholders", not warnings, "critical", "Required secrets are configured.", "; ".join(warnings) or "No action required."),
        _item("JWT secret key strong enough", not any("JWT_SECRET_KEY" in warning for warning in warnings), "critical", "JWT secret key strength was checked.", "Use a random secret of at least 32 characters."),
        _item("HTTPS configured in Nginx", "listen 443 ssl" in nginx_text and "ssl_protocols TLSv1.2 TLSv1.3" in nginx_text, "high", "Nginx HTTPS and TLS versions are configured.", "Configure TLSv1.2/TLSv1.3 with valid certificates."),
        _item("Database not exposed on public port", "5432:5432" not in Path("deployment/docker-compose.prod.yml").read_text() if Path("deployment/docker-compose.prod.yml").exists() else True, "medium", "Production database port is not published.", "Avoid exposing Postgres publicly."),
    ]
    critical = sum(1 for check in checks if check.status == "FAIL" and check.severity == "critical")
    high = sum(1 for check in checks if check.status == "FAIL" and check.severity == "high")
    medium = sum(1 for check in checks if check.status == "FAIL" and check.severity == "medium")
    overall = "PASS" if critical == 0 and high == 0 else "FAIL"
    return SecurityChecklistReport(
        checks=checks,
        critical_failures=critical,
        high_failures=high,
        medium_failures=medium,
        overall_status=overall,
        generated_at=datetime.now(timezone.utc),
    )


def check_for_vulnerable_dependencies(requirements_path: str = "backend/requirements.txt") -> list[dict]:
    vulnerable = {
        "pyjwt": "Use python-jose already configured; avoid outdated PyJWT versions.",
        "django": "Not used by this project; pin to supported versions if added.",
    }
    findings = []
    try:
        for line in Path(requirements_path).read_text().splitlines():
            package = line.strip().split("==")[0].split("<")[0].split(">")[0].lower()
            if package in vulnerable:
                findings.append({"package": package, "description": vulnerable[package], "severity": "medium"})
    except Exception:
        return [{"package": "requirements.txt", "description": "Could not read requirements.txt", "severity": "low"}]
    return findings


async def generate_security_report() -> SecurityChecklistReport:
    return await run_security_checklist()
