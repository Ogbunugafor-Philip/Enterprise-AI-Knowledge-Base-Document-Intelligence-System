from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ChatSessionCreate(BaseModel):
    title: str | None = None


class ChatSessionResponse(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int


class ChatSessionListResponse(BaseModel):
    sessions: list[ChatSessionResponse]
    total: int


class MessageCreate(BaseModel):
    content: str = Field(min_length=1)


class SourceDocument(BaseModel):
    document_id: UUID | str
    document_title: str
    chunk_text: str
    relevance_score: float
    page_number: int | None = None


class MessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    source_documents: list[SourceDocument] | list[dict] | None
    confidence_score: float | None
    retrieval_score: float | None
    hallucination_risk_score: float | None
    response_rejected: bool
    feedback: str | None
    created_at: datetime


class AskQuestionRequest(BaseModel):
    session_id: UUID | None = None
    question: str = Field(min_length=1)


class AskQuestionResponse(BaseModel):
    message_id: UUID
    answer: str
    source_documents: list[SourceDocument] | list[dict]
    confidence_score: float
    retrieval_score: float
    hallucination_risk_score: float
    response_rejected: bool
    fallback_message: str | None = None


class FeedbackRequest(BaseModel):
    message_id: UUID
    feedback_type: str = Field(pattern="^(correct|incorrect|unclear|hallucination)$")
    feedback_note: str | None = None


class FeedbackResponse(BaseModel):
    message_id: UUID
    feedback_type: str
    submitted_at: datetime


class ChatSearchRequest(BaseModel):
    query: str
    limit: int = 20
    offset: int = 0


class ChatSearchResponse(BaseModel):
    sessions: list[ChatSessionResponse]
    messages: list[MessageResponse]
    total_results: int


class SampleQuestionsResponse(BaseModel):
    department: str | None
    role: str | None
    questions: list[str]


class OnboardingStatusResponse(BaseModel):
    is_completed: bool
    current_step: int
    total_steps: int


class OnboardingStepRequest(BaseModel):
    step_number: int = Field(ge=1, le=5)
