from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentApprovalRequest(BaseModel):
    document_id: UUID
    action: str = Field(..., pattern="^(approve|reject)$")
    rejection_reason: str | None = None
    access_level: str = Field(default="organization", pattern="^(organization|department|role|user)$")


class DocumentApprovalResponse(BaseModel):
    document_id: UUID
    file_name: str
    status: str
    approved_by: UUID | None
    approved_at: datetime | None
    rejection_reason: str | None


class DocumentVersionCreate(BaseModel):
    parent_document_id: UUID
    title: str
    description: str | None = None
    department_id: UUID | None = None


class DocumentVersionResponse(BaseModel):
    id: UUID
    title: str
    version_number: int
    parent_document_id: UUID | None
    status: str
    created_at: datetime


class DocumentVersionListResponse(BaseModel):
    versions: list[DocumentVersionResponse]
    current_version: DocumentVersionResponse | None
    total_versions: int


class DocumentAccessRuleCreate(BaseModel):
    document_id: UUID
    access_type: str = Field(..., pattern="^(organization|department|role|user)$")
    department_id: UUID | None = None
    role_id: UUID | None = None
    user_id: UUID | None = None


class DocumentAccessRuleResponse(BaseModel):
    id: UUID
    document_id: UUID
    access_type: str
    department_id: UUID | None
    role_id: UUID | None
    user_id: UUID | None
    granted_by: UUID | None
    granted_at: datetime


class ApprovalQueueResponse(BaseModel):
    documents: list[dict]
    total_pending: int
    total_reviewed: int
    page: int
    page_size: int


class KnowledgeGovernanceStats(BaseModel):
    total_approved: int
    total_rejected: int
    total_pending_review: int
    approval_rate_percent: float
    avg_approval_time_hours: float
    most_active_reviewer: str | None
