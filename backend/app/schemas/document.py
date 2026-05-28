from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    id: UUID
    title: str
    file_name: str
    file_type: str
    file_size_mb: float
    status: str
    malware_scan_status: str
    created_at: datetime


class DocumentResponse(BaseModel):
    id: UUID
    title: str
    description: str | None
    file_name: str
    file_type: str
    file_size_mb: float
    status: str
    is_approved: bool
    approved_by: UUID | None
    approved_at: datetime | None
    version_number: int
    chunk_count: int
    embedding_status: str
    malware_scan_status: str
    malware_scan_result: str | None
    uploaded_by: UUID
    department_id: UUID | None
    organization_id: UUID
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int
    page: int
    page_size: int


class DocumentStatusResponse(BaseModel):
    id: UUID
    file_name: str
    status: str
    malware_scan_status: str
    embedding_status: str
    chunk_count: int
    error_message: str | None = None
    updated_at: datetime


class DocumentFilterRequest(BaseModel):
    status: str | None = None
    file_type: str | None = None
    department_id: UUID | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    search_query: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class IngestionStatusResponse(BaseModel):
    document_id: UUID
    file_name: str
    current_stage: str
    progress_percent: int
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None


class FailedUploadResponse(BaseModel):
    id: UUID
    file_name: str
    failure_reason: str | None
    failure_stage: str | None
    created_at: datetime


class AdminDashboardStats(BaseModel):
    total_documents: int
    pending_approval: int
    approved_documents: int
    failed_uploads: int
    total_chunks: int
    documents_by_status: dict[str, int]
    documents_by_type: dict[str, int]
    recent_uploads: list[DocumentResponse]
