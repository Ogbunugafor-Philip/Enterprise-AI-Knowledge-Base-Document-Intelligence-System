from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ScoredChunk(BaseModel):
    chunk_id: str
    document_id: str
    document_title: str
    chunk_text: str
    relevance_score: float
    chunk_index: int


class RAGSourceDocument(BaseModel):
    document_id: str
    document_title: str
    chunk_text: str
    relevance_score: float
    chunk_index: int
    page_number: int | None = None


class RAGResponse(BaseModel):
    answer: str
    source_documents: list[RAGSourceDocument]
    retrieval_confidence: float
    response_confidence: float
    hallucination_risk: float
    response_rejected: bool
    fallback_message: str | None = None
    token_usage: dict
    processing_time_ms: int


class RAGQualityMetrics(BaseModel):
    retrieval_confidence: float
    response_confidence: float
    hallucination_risk: float
    chunks_retrieved: int
    chunks_used: int
    token_usage: dict
    processing_time_ms: int


class LowConfidenceFlag(BaseModel):
    document_id: str | None
    question: str
    confidence_score: float
    hallucination_risk: float
    flagged_at: datetime
    reviewed: bool
