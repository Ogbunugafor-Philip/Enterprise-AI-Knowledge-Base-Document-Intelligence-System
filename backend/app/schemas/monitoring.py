from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ErrorTrendPoint(BaseModel):
    timestamp: str
    error_count: int
    endpoint: str | None = None


class ResponseTimeTrendPoint(BaseModel):
    timestamp: str
    avg_response_time_ms: float


class AIQualityTrendPoint(BaseModel):
    date: str
    avg_confidence: float
    avg_hallucination_risk: float
    rejection_count: int


class SystemMetricsResponse(BaseModel):
    total_api_calls: int
    failed_api_calls: int
    error_rate_percent: float
    avg_response_time_ms: float
    total_ai_queries: int
    failed_ai_calls: int
    total_token_usage: int
    total_document_uploads: int
    failed_document_ingestion: int
    total_login_events: int
    failed_login_events: int
    active_users: int
    period: str


class AlertResponse(BaseModel):
    id: UUID
    alert_type: str
    severity: str
    title: str
    description: str | None
    affected_service: str | None
    status: str
    recommended_action: str | None
    business_impact: str | None
    created_at: datetime
    updated_at: datetime


class AlertUpdateRequest(BaseModel):
    status: str
    resolution_notes: str | None = None


class IncidentResponse(BaseModel):
    id: UUID
    title: str
    description: str | None
    severity: str
    status: str
    affected_services: dict | list | None
    error_count: int
    first_occurrence: datetime | None
    last_occurrence: datetime | None
    root_cause: str | None
    resolution_steps: str | None
    business_impact: str | None


class DebuggingAnalysis(BaseModel):
    plain_english_explanation: str
    possible_cause: str
    affected_service: str
    affected_endpoint: str | None = None
    business_impact: str
    recommended_steps: list[str]
    severity: str


class SystemHealthSummary(BaseModel):
    summary_text: str
    risk_level: str
    generated_at: datetime


class AITrustReport(BaseModel):
    avg_confidence_score: float
    avg_hallucination_risk: float
    total_responses: int
    rejected_responses: int
    rejection_rate_percent: float
    problematic_documents: list[dict]
    trust_level: str
    report_text: str
    generated_at: datetime


class MonitoringDashboardData(BaseModel):
    system_metrics: SystemMetricsResponse
    active_alerts: list[AlertResponse]
    health_summary: SystemHealthSummary | None
    ai_quality_trend: list[AIQualityTrendPoint]
    response_time_trend: list[ResponseTimeTrendPoint]
    error_trend: list[ErrorTrendPoint]
    top_endpoints: list[dict]
