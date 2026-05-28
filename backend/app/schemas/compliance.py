from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AuditLogResponse(BaseModel):
    id: UUID
    user_id: UUID | None
    user_email_masked: str | None = None
    organization_id: UUID | None
    action: str
    resource_type: str
    resource_id: str | None
    ip_address: str | None
    status: str
    created_at: datetime


class AuditLogDetailResponse(AuditLogResponse):
    old_value: dict | list | None
    new_value: dict | list | None
    user_agent: str | None
    previous_hash: str | None = None
    audit_hash: str | None = None


class AuditLogListResponse(BaseModel):
    logs: list[AuditLogResponse]
    total_count: int
    page: int
    page_size: int


class AuditLogFilterRequest(BaseModel):
    user_id: UUID | None = None
    action: str | None = None
    resource_type: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class ComplianceReport(BaseModel):
    report_type: str
    organization_id: UUID | None
    date_from: datetime | None
    date_to: datetime | None
    generated_at: datetime
    generated_by: UUID
    summary: dict
    data: dict | list


class ComplianceReportRequest(BaseModel):
    report_type: str = Field(..., pattern="^(activity|access|document|security)$")
    date_from: datetime | None = None
    date_to: datetime | None = None
    format: str = Field(default="pdf", pattern="^(pdf|csv)$")


class DataRetentionSettings(BaseModel):
    chat_retention_days: int = Field(default=365, ge=1)
    document_retention_days: int = Field(default=2555, ge=1)
    monitoring_log_retention_days: int = Field(default=90, ge=1)
    audit_log_retention_days: int = Field(default=2555, ge=1)


class UserDataExport(BaseModel):
    user_id: UUID
    export_date: datetime
    profile_data: dict
    chat_history: list[dict]
    ai_queries: list[dict]
    audit_entries: list[dict]
