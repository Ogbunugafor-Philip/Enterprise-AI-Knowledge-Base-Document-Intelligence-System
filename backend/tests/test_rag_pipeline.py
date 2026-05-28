import asyncio
from types import SimpleNamespace
from uuid import uuid4

from app.core.rag_config import FALLBACK_MESSAGE, MAX_HALLUCINATION_RISK, MIN_RESPONSE_CONFIDENCE
from app.schemas.rag import ScoredChunk
from app.services.ai_guard_service import enforce_no_source_no_answer, get_fallback_message
from app.services.rag_service import (
    build_rag_prompt,
    calculate_hallucination_risk,
    calculate_response_confidence,
    calculate_retrieval_confidence,
    extract_answer_and_sources,
    should_reject_response,
)
from app.services.vector_search_service import format_context_for_llm


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _chunk(score: float = 0.85, doc_id: str | None = None, text: str = "Policy states X.") -> ScoredChunk:
    return ScoredChunk(
        chunk_id=str(uuid4()),
        document_id=doc_id or str(uuid4()),
        document_title="Test Policy Document",
        chunk_text=text,
        relevance_score=score,
        chunk_index=0,
    )


class FakeDB:
    def __init__(self):
        self.added = []

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        pass

    async def execute(self, query):
        return SimpleNamespace(scalar_one_or_none=lambda: None, scalar_one=lambda: 0)

    async def scalar(self, query):
        return 0


# ---------------------------------------------------------------------------
# build_rag_prompt
# ---------------------------------------------------------------------------

def test_build_rag_prompt_returns_non_empty_system_and_user_prompts():
    chunks = [_chunk()]
    context, _ = format_context_for_llm(chunks)
    system, user = build_rag_prompt("What is the policy?", chunks, context)

    assert len(system) > 0
    assert len(user) > 0


def test_build_rag_prompt_includes_no_outside_knowledge_instruction():
    chunks = [_chunk()]
    context, _ = format_context_for_llm(chunks)
    system, _ = build_rag_prompt("Tell me about leave policy", chunks, context)

    lower = system.lower()
    assert any(phrase in lower for phrase in [
        "outside knowledge",
        "never use",
        "only from",
        "only answer",
        "provided context",
    ])


def test_build_rag_prompt_includes_citation_instruction():
    chunks = [_chunk()]
    context, _ = format_context_for_llm(chunks)
    system, _ = build_rag_prompt("What are the rules?", chunks, context)

    assert "cite" in system.lower() or "source" in system.lower()


def test_build_rag_prompt_includes_fallback_instruction():
    chunks = [_chunk()]
    context, _ = format_context_for_llm(chunks)
    system, _ = build_rag_prompt("Unknown topic", chunks, context)

    lower = system.lower()
    assert "cannot find" in lower or "i cannot" in lower or "not contain" in lower


# ---------------------------------------------------------------------------
# calculate_retrieval_confidence
# ---------------------------------------------------------------------------

def test_calculate_retrieval_confidence_returns_zero_for_empty_chunks():
    score = calculate_retrieval_confidence([])
    assert score == 0.0


def test_calculate_retrieval_confidence_returns_value_between_0_and_1_for_valid_chunks():
    chunks = [_chunk(0.85), _chunk(0.72), _chunk(0.90)]
    score = calculate_retrieval_confidence(chunks, top_k=5)

    assert 0.0 <= score <= 1.0


def test_calculate_retrieval_confidence_higher_for_better_scores():
    low_chunks = [_chunk(0.2), _chunk(0.3)]
    high_chunks = [_chunk(0.9), _chunk(0.95)]

    low_score = calculate_retrieval_confidence(low_chunks)
    high_score = calculate_retrieval_confidence(high_chunks)

    assert high_score > low_score


# ---------------------------------------------------------------------------
# calculate_hallucination_risk
# ---------------------------------------------------------------------------

def test_calculate_hallucination_risk_returns_higher_risk_for_empty_context():
    risk_with_no_context = calculate_hallucination_risk(
        retrieval_confidence=0.0,
        answer="The policy is X.",
        context="",
    )
    risk_with_good_context = calculate_hallucination_risk(
        retrieval_confidence=0.9,
        answer="The policy is X.",
        context="The policy is X. This is a well grounded statement.",
    )

    assert risk_with_no_context > risk_with_good_context


def test_calculate_hallucination_risk_stays_between_0_and_1():
    risk = calculate_hallucination_risk(
        retrieval_confidence=0.5,
        answer="Some answer here.",
        context="Some context here.",
    )
    assert 0.0 <= risk <= 1.0


def test_calculate_hallucination_risk_high_when_confidence_zero():
    risk = calculate_hallucination_risk(
        retrieval_confidence=0.0,
        answer="",
        context="",
    )
    assert risk >= 0.9


# ---------------------------------------------------------------------------
# should_reject_response
# ---------------------------------------------------------------------------

def test_should_reject_response_returns_true_for_low_confidence_and_high_risk():
    assert should_reject_response(
        response_confidence=0.3,
        hallucination_risk=0.8,
        retrieval_confidence=0.6,
    ) is True


def test_should_reject_response_returns_false_for_good_scores():
    assert should_reject_response(
        response_confidence=0.8,
        hallucination_risk=0.2,
        retrieval_confidence=0.7,
    ) is False


def test_should_reject_response_returns_true_when_only_confidence_is_low():
    assert should_reject_response(
        response_confidence=0.3,
        hallucination_risk=0.3,
        retrieval_confidence=0.7,
    ) is True


def test_should_reject_response_returns_true_when_only_hallucination_risk_is_high():
    assert should_reject_response(
        response_confidence=0.8,
        hallucination_risk=0.9,
        retrieval_confidence=0.7,
    ) is True


def test_should_reject_response_returns_true_when_only_retrieval_confidence_is_low():
    assert should_reject_response(
        response_confidence=0.8,
        hallucination_risk=0.2,
        retrieval_confidence=0.2,
    ) is True


# ---------------------------------------------------------------------------
# format_context_for_llm
# ---------------------------------------------------------------------------

def test_format_context_for_llm_returns_formatted_string_with_document_references():
    chunks = [_chunk(0.85, text="Leave policy allows 20 days annually.")]
    context_str, sources = format_context_for_llm(chunks)

    assert "Test Policy Document" in context_str
    assert "Leave policy allows 20 days annually." in context_str
    assert len(sources) == 1
    assert sources[0]["document_title"] == "Test Policy Document"


def test_format_context_for_llm_returns_empty_string_for_no_chunks():
    context_str, sources = format_context_for_llm([])

    assert context_str == ""
    assert sources == []


def test_format_context_for_llm_includes_relevance_score():
    chunks = [_chunk(0.92)]
    context_str, _ = format_context_for_llm(chunks)

    assert "0.92" in context_str


def test_format_context_for_llm_separates_multiple_chunks():
    chunks = [_chunk(0.9, text="First chunk."), _chunk(0.8, text="Second chunk.")]
    context_str, sources = format_context_for_llm(chunks)

    assert "First chunk." in context_str
    assert "Second chunk." in context_str
    assert len(sources) == 2


# ---------------------------------------------------------------------------
# enforce_no_source_no_answer
# ---------------------------------------------------------------------------

def test_enforce_no_source_no_answer_blocks_response_when_chunks_list_is_empty():
    blocked, fallback = enforce_no_source_no_answer([])

    assert blocked is True
    assert fallback is not None


def test_enforce_no_source_no_answer_blocks_when_all_scores_below_threshold():
    sources = [{"relevance_score": 0.1}, {"relevance_score": 0.2}]
    blocked, fallback = enforce_no_source_no_answer(sources)

    assert blocked is True


# ---------------------------------------------------------------------------
# get_fallback_message
# ---------------------------------------------------------------------------

def test_get_fallback_message_returns_the_configured_fallback_string():
    msg = get_fallback_message()

    assert len(msg) > 20
    assert isinstance(msg, str)


# ---------------------------------------------------------------------------
# flag_low_confidence_response (no live DB)
# ---------------------------------------------------------------------------

def test_flag_low_confidence_response_creates_system_alert_for_low_confidence():
    from app.services.rag_logging_service import flag_low_confidence_response

    db = FakeDB()
    org_id = uuid4()

    asyncio.run(
        flag_low_confidence_response(
            db=db,
            organization_id=org_id,
            question="What is the leave policy?",
            response_confidence=0.2,
            hallucination_risk=0.8,
            source_document_ids=[str(uuid4())],
        )
    )

    alert_added = any(
        hasattr(obj, "alert_type") and obj.alert_type == "low_confidence_ai_response"
        for obj in db.added
    )
    assert alert_added


def test_flag_low_confidence_response_does_not_create_alert_for_good_scores():
    from app.services.rag_logging_service import flag_low_confidence_response

    db = FakeDB()
    org_id = uuid4()

    asyncio.run(
        flag_low_confidence_response(
            db=db,
            organization_id=org_id,
            question="What is the leave policy?",
            response_confidence=0.9,
            hallucination_risk=0.1,
            source_document_ids=[str(uuid4())],
        )
    )

    alert_added = any(hasattr(obj, "alert_type") for obj in db.added)
    assert not alert_added


# ---------------------------------------------------------------------------
# extract_answer_and_sources
# ---------------------------------------------------------------------------

def test_extract_answer_and_sources_returns_clean_answer():
    sources = [{"document_title": "HR Manual", "document_id": str(uuid4()), "chunk_text": "test", "relevance_score": 0.9, "chunk_index": 0}]
    answer, cited = extract_answer_and_sources("Based on HR Manual, the answer is X.", sources)

    assert "HR Manual" in answer
    assert len(cited) > 0


def test_extract_answer_and_sources_falls_back_to_all_sources_when_none_cited():
    sources = [{"document_title": "Policy Doc", "document_id": str(uuid4()), "chunk_text": "test", "relevance_score": 0.8, "chunk_index": 0}]
    answer, cited = extract_answer_and_sources("Some answer without citing any document.", sources)

    assert cited == sources
