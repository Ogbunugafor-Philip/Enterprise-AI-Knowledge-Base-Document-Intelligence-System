from typing import Any

from app.models.document import Document
from app.models.user import User
from app.services.approval_service import enforce_approval_gate

MIN_RETRIEVAL_THRESHOLD = 0.5

_INELIGIBLE_STATUSES = {"uploaded", "processing", "reviewed", "rejected", "archived", "deleted", "failed", "expired"}


async def validate_document_eligibility(db, user: User, document: Document) -> tuple[bool, str]:
    if not enforce_approval_gate(document):
        return False, "Document has not passed the approval gate"
    if document.status in _INELIGIBLE_STATUSES:
        return False, "Document is not eligible for retrieval"
    from app.services.access_rule_service import check_user_document_access

    if not await check_user_document_access(db, user, document):
        return False, "User does not have access to this document"
    return True, "eligible"


def get_fallback_message() -> str:
    return (
        "I could not find enough reliable information in approved source documents "
        "to answer that safely. Try rephrasing the question or contact your administrator."
    )


def enforce_no_source_no_answer(source_documents: list[dict[str, Any]]) -> tuple[bool, str | None]:
    if not source_documents:
        return True, get_fallback_message()
    best_score = max(float(source.get("relevance_score", 0.0)) for source in source_documents)
    if best_score < MIN_RETRIEVAL_THRESHOLD:
        return True, get_fallback_message()
    return False, None


def calculate_retrieval_score(source_documents: list[dict[str, Any]]) -> float:
    if not source_documents:
        return 0.0
    scores = [float(source.get("relevance_score", 0.0)) for source in source_documents]
    return max(0.0, min(1.0, sum(scores) / len(scores)))


def calculate_confidence_score(source_documents: list[dict[str, Any]], answer: str | None = None) -> float:
    retrieval_score = calculate_retrieval_score(source_documents)
    answer_factor = 1.0 if answer and len(answer.strip()) >= 20 else 0.8
    return max(0.0, min(1.0, retrieval_score * answer_factor))


def calculate_hallucination_risk(confidence_score: float, retrieval_score: float) -> float:
    return max(0.0, min(1.0, 1.0 - ((confidence_score + retrieval_score) / 2)))


def should_reject_response(confidence_score: float, hallucination_risk: float) -> bool:
    return confidence_score < 0.5 or hallucination_risk > 0.7


async def filter_eligible_documents(db, user: User, retrieved_chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    eligible_chunks: list[dict[str, Any]] = []
    for chunk in retrieved_chunks:
        document = chunk.get("document")
        if document is None:
            continue
        is_eligible, _ = await validate_document_eligibility(db, user, document)
        if is_eligible:
            eligible_chunks.append(chunk)
    return eligible_chunks
