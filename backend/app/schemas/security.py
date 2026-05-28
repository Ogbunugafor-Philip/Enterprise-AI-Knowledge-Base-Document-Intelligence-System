from datetime import datetime

from pydantic import BaseModel


class SecurityCheckItem(BaseModel):
    check_name: str
    status: str
    severity: str
    description: str
    recommendation: str


class SecurityChecklistReport(BaseModel):
    checks: list[SecurityCheckItem]
    critical_failures: int
    high_failures: int
    medium_failures: int
    overall_status: str
    generated_at: datetime


class RateLimitStatus(BaseModel):
    endpoint: str
    limit: int
    remaining: int
    reset_at: datetime


class SecurityEvent(BaseModel):
    event_type: str
    severity: str
    ip_address: str | None
    endpoint: str | None
    description: str | None
    created_at: datetime
