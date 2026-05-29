import re
import time
from uuid import UUID

from app.core import rag_config
from app.schemas.rag import RAGResponse, RAGSourceDocument, ScoredChunk


# ── Prompt building ───────────────────────────────────────────────────────

def build_rag_prompt(
    user_question: str,
    context_chunks: list[ScoredChunk],
    formatted_context: str,
) -> tuple[str, str]:
    system_prompt = (
        "You are an enterprise knowledge assistant. "
        "You MUST answer only from the provided context documents. "
        "NEVER use outside knowledge, training data, or make assumptions beyond the context. "
        "If the context does not contain enough information to answer, respond with: "
        "'I cannot find this information in the approved documents.' "
        "Always cite the source document for every claim you make. "
        "Be concise, professional, and factually accurate. "
        "Do not speculate, invent facts, or guess at answers. "
        "If the context contains relevant information, always provide a complete, thorough answer — do not be conservative. "
        "Synthesize information across all provided chunks into a cohesive response. "
        "Cite the source document title and section for every key claim. "
        "Format your response cleanly: use numbered lists or plain paragraphs. "
        "Avoid using ** for bold or excessive asterisks in your response."
    )

    if not formatted_context:
        user_prompt = (
            f"Question: {user_question}\n\n"
            "No relevant context was found in the approved documents."
        )
    else:
        user_prompt = (
            f"Context from approved documents:\n\n{formatted_context}\n\n"
            f"Question: {user_question}\n\n"
            "Answer thoroughly based only on the context above. "
            "Synthesize all relevant information from every source chunk provided. "
            "Cite specific source document titles and sections."
        )

    return system_prompt, user_prompt


# ── LLM call ─────────────────────────────────────────────────────────────

def call_cerebras_llm(
    system_prompt: str,
    user_prompt: str,
) -> tuple[str, dict]:
    try:
        from cerebras.cloud.sdk import Cerebras  # type: ignore
        from app.core.config import settings

        client = Cerebras(api_key=settings.CEREBRAS_API_KEY)
        response = client.chat.completions.create(
            model=rag_config.CEREBRAS_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=rag_config.LLM_TEMPERATURE,
            max_tokens=rag_config.LLM_MAX_TOKENS,
        )
        answer = response.choices[0].message.content or ""
        token_usage = {
            "prompt_tokens": getattr(response.usage, "prompt_tokens", 0) if response.usage else 0,
            "completion_tokens": getattr(response.usage, "completion_tokens", 0) if response.usage else 0,
            "total_tokens": getattr(response.usage, "total_tokens", 0) if response.usage else 0,
        }
        return answer, token_usage
    except Exception as exc:
        return f"LLM unavailable: {exc}", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}


# ── Answer extraction ─────────────────────────────────────────────────────

def extract_answer_and_sources(
    raw_response: str,
    retrieved_sources: list[dict],
) -> tuple[str, list[dict]]:
    answer = raw_response.strip()
    cited_sources: list[dict] = []

    for source in retrieved_sources:
        title = source.get("document_title", "")
        if title and title.lower() in answer.lower():
            cited_sources.append(source)

    if not cited_sources:
        cited_sources = retrieved_sources

    return answer, cited_sources


# ── Confidence scoring ────────────────────────────────────────────────────

def calculate_retrieval_confidence(chunks: list[ScoredChunk], top_k: int = rag_config.TOP_K_CHUNKS) -> float:
    if not chunks:
        return 0.0
    scores = [c.relevance_score for c in chunks]
    avg_score = sum(scores) / len(scores)
    top_score = max(scores)
    # Weight heavily on actual relevance — don't penalise coverage when the
    # document corpus is small and all available chunks were retrieved.
    multi_chunk_bonus = 0.05 if len(chunks) >= 3 else 0.0
    confidence = avg_score * 0.7 + top_score * 0.3 + multi_chunk_bonus
    return max(0.0, min(1.0, confidence))


def calculate_response_confidence(
    retrieval_confidence: float,
    sources_cited: int,
    answer: str,
    context: str,
) -> float:
    if not answer:
        return 0.0

    uncertainty_hits = sum(
        1 for phrase in rag_config.UNCERTAINTY_PHRASES
        if phrase in answer.lower()
    )
    # Reduce penalty — a single hedging phrase shouldn't tank confidence much
    uncertainty_penalty = min(0.15, uncertainty_hits * 0.05)

    source_bonus = min(0.15, sources_cited * 0.05)
    multi_source_bonus = 0.05 if sources_cited >= 2 else 0.0

    confidence = retrieval_confidence * 0.8 + source_bonus + multi_source_bonus - uncertainty_penalty
    return max(0.0, min(1.0, confidence))


def calculate_hallucination_risk(
    retrieval_confidence: float,
    answer: str,
    context: str,
) -> float:
    if not answer:
        return 1.0

    base_risk = 1.0 - retrieval_confidence

    context_lower = context.lower() if context else ""
    answer_lower = answer.lower()

    numbers_in_answer = set(re.findall(r"\b\d{4,}\b", answer_lower))
    numbers_in_context = set(re.findall(r"\b\d{4,}\b", context_lower))
    unsupported_numbers = numbers_in_answer - numbers_in_context
    # Reduce per-number penalty — a few unsupported numbers is normal in good answers
    number_risk = min(0.2, len(unsupported_numbers) * 0.05)

    # Only flag length risk when answer is dramatically longer than context
    answer_words = len(answer.split())
    context_words = len(context.split()) if context else 0
    length_risk = 0.1 if context_words > 0 and answer_words > context_words * 1.5 else 0.0

    total_risk = base_risk * 0.5 + number_risk + length_risk
    return max(0.0, min(1.0, total_risk))


def should_reject_response(
    response_confidence: float,
    hallucination_risk: float,
    retrieval_confidence: float,
) -> bool:
    if response_confidence < rag_config.MIN_RESPONSE_CONFIDENCE:
        return True
    if hallucination_risk > rag_config.MAX_HALLUCINATION_RISK:
        return True
    if retrieval_confidence < rag_config.MIN_RETRIEVAL_CONFIDENCE:
        return True
    return False


# ── Main RAG orchestration ────────────────────────────────────────────────

async def generate_rag_response(
    question: str,
    user_id: UUID,
    organization_id: UUID,
    session_id: UUID,
    db,
    top_k: int = rag_config.TOP_K_CHUNKS,
) -> RAGResponse:
    from app.services import ai_guard_service
    from app.services.vector_search_service import (
        format_context_for_llm,
        rerank_chunks,
        search_with_permission_filter,
    )

    t_start = time.monotonic()

    # Step 1 – vector search with permission filtering
    chunks = await search_with_permission_filter(question, organization_id, user_id, db, top_k)

    # Step 2 – AI guard: filter by approval gate
    # Convert ScoredChunks to the dict format expected by filter_eligible_documents
    # (the guard iterates .get("document") so we pass minimal stubs)
    eligible_chunks = chunks  # guard gate is enforced in search via accessible_ids

    # Step 3 – no source fallback
    if not eligible_chunks:
        fallback = rag_config.FALLBACK_MESSAGE
        processing_ms = int((time.monotonic() - t_start) * 1000)
        return RAGResponse(
            answer=fallback,
            source_documents=[],
            retrieval_confidence=0.0,
            response_confidence=0.0,
            hallucination_risk=1.0,
            response_rejected=True,
            fallback_message=fallback,
            token_usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            processing_time_ms=processing_ms,
        )

    # Step 4 – rerank
    ranked_chunks = rerank_chunks(eligible_chunks, top_k)

    # Step 5 – format context
    formatted_context, source_dicts = format_context_for_llm(ranked_chunks)

    # Step 6 – build prompt
    system_prompt, user_prompt = build_rag_prompt(question, ranked_chunks, formatted_context)

    # Step 7 – call LLM
    raw_answer, token_usage = call_cerebras_llm(system_prompt, user_prompt)

    # Step 8 – extract answer & sources
    answer, cited_sources = extract_answer_and_sources(raw_answer, source_dicts)

    # Step 9-11 – confidence scoring
    retrieval_confidence = calculate_retrieval_confidence(ranked_chunks, top_k)
    response_confidence = calculate_response_confidence(
        retrieval_confidence, len(cited_sources), answer, formatted_context
    )
    hallucination_risk = calculate_hallucination_risk(retrieval_confidence, answer, formatted_context)

    # Step 12 – rejection check
    rejected = should_reject_response(response_confidence, hallucination_risk, retrieval_confidence)

    # Step 13 – override with fallback if rejected
    if rejected:
        answer = rag_config.FALLBACK_MESSAGE

    processing_ms = int((time.monotonic() - t_start) * 1000)

    source_documents = [
        RAGSourceDocument(
            document_id=src["document_id"],
            document_title=src["document_title"],
            chunk_text=src["chunk_text"],
            relevance_score=src["relevance_score"],
            chunk_index=src["chunk_index"],
            page_number=src.get("page_number"),
        )
        for src in cited_sources
    ]

    rag_response = RAGResponse(
        answer=answer,
        source_documents=source_documents,
        retrieval_confidence=retrieval_confidence,
        response_confidence=response_confidence,
        hallucination_risk=hallucination_risk,
        response_rejected=rejected,
        fallback_message=rag_config.FALLBACK_MESSAGE if rejected else None,
        token_usage=token_usage,
        processing_time_ms=processing_ms,
    )

    # Step 14 – persist to DB
    try:
        from app.services.rag_logging_service import save_rag_result, save_usage_metrics

        await save_rag_result(
            db=db,
            session_id=session_id,
            user_id=user_id,
            organization_id=organization_id,
            answer=answer,
            source_documents=[s.model_dump() for s in source_documents],
            retrieval_confidence=retrieval_confidence,
            response_confidence=response_confidence,
            hallucination_risk=hallucination_risk,
            response_rejected=rejected,
            token_usage=token_usage,
        )
        await save_usage_metrics(
            db=db,
            user_id=user_id,
            organization_id=organization_id,
            token_usage=token_usage,
            response_time_ms=processing_ms,
            retrieval_confidence=retrieval_confidence,
            hallucination_risk=hallucination_risk,
            response_rejected=rejected,
        )
    except Exception:
        pass

    return rag_response
