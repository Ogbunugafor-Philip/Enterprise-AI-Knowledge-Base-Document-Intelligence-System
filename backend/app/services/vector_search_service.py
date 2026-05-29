from functools import lru_cache
from uuid import UUID

from app.core.rag_config import TOP_K_CHUNKS
from app.schemas.rag import ScoredChunk
from app.services.embedding_service import generate_embedding


@lru_cache(maxsize=1)
def initialize_qdrant_client():
    try:
        from qdrant_client import QdrantClient  # type: ignore

        from app.core.config import settings

        return QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT, timeout=10)
    except Exception:
        return None


async def search_similar_chunks(
    query_text: str,
    organization_id: UUID,
    user_id: UUID,
    db,
    top_k: int = TOP_K_CHUNKS,
) -> list[ScoredChunk]:
    client = initialize_qdrant_client()
    if client is None:
        return []

    try:
        from qdrant_client.models import FieldCondition, Filter, MatchValue  # type: ignore

        from app.services.access_rule_service import get_user_accessible_document_ids

        accessible_ids = await get_user_accessible_document_ids(db, _stub_user(user_id, organization_id))
        accessible_str = [str(doc_id) for doc_id in accessible_ids]

        query_vector = generate_embedding(query_text)
        if hasattr(query_vector, "tolist"):
            query_vector = query_vector.tolist()
        else:
            query_vector = list(query_vector)

        from app.services.embedding_service import QDRANT_COLLECTION
        collection_name = QDRANT_COLLECTION

        must_filters = [
            FieldCondition(key="organization_id", match=MatchValue(value=str(organization_id)))
        ]

        response = client.query_points(
            collection_name=collection_name,
            query=query_vector,
            query_filter=Filter(must=must_filters),
            limit=top_k * 2,
            with_payload=True,
        )

        chunks: list[ScoredChunk] = []
        for hit in response.points:
            payload = hit.payload or {}
            doc_id = payload.get("document_id", "")
            if accessible_ids and doc_id not in accessible_str:
                continue
            chunks.append(
                ScoredChunk(
                    chunk_id=payload.get("chunk_id", str(hit.id)),
                    document_id=doc_id,
                    document_title=payload.get("document_title", "Unknown Document"),
                    chunk_text=payload.get("chunk_text", ""),
                    relevance_score=float(hit.score),
                    chunk_index=int(payload.get("chunk_index", 0)),
                )
            )
        return chunks[:top_k]
    except Exception:
        return []


class _stub_user:
    """Minimal user-like object for service calls that need user.organization_id."""
    def __init__(self, user_id: UUID, organization_id: UUID):
        self.id = user_id
        self.organization_id = organization_id
        self.department_id = None
        self.role_id = None
        self.role = None


async def search_with_permission_filter(
    query_text: str,
    organization_id: UUID,
    user_id: UUID,
    db,
    top_k: int = TOP_K_CHUNKS,
) -> list[ScoredChunk]:
    chunks = await search_similar_chunks(query_text, organization_id, user_id, db, top_k)
    return chunks


def rerank_chunks(chunks: list[ScoredChunk], top_k: int = TOP_K_CHUNKS) -> list[ScoredChunk]:
    if not chunks:
        return []

    # Deduplicate by exact (document_id, chunk_index) pair so the same chunk
    # is never returned twice, but all distinct chunks are allowed through.
    # Positional-window deduplication (the old // 3 approach) was discarding
    # valid, distinct chunks from small documents.
    seen: set[tuple[str, int]] = set()
    deduplicated: list[ScoredChunk] = []

    for chunk in sorted(chunks, key=lambda c: c.relevance_score, reverse=True):
        key = (chunk.document_id, chunk.chunk_index)
        if key not in seen:
            seen.add(key)
            deduplicated.append(chunk)

    return deduplicated[:top_k]


def format_context_for_llm(chunks: list[ScoredChunk]) -> tuple[str, list[dict]]:
    if not chunks:
        return "", []

    parts: list[str] = []
    sources: list[dict] = []

    for i, chunk in enumerate(chunks, start=1):
        section = (
            f"[Source {i}] Document: {chunk.document_title} | "
            f"Section {chunk.chunk_index + 1} | "
            f"Relevance: {chunk.relevance_score:.2f}\n"
            f"{chunk.chunk_text.strip()}"
        )
        parts.append(section)
        sources.append(
            {
                "document_id": chunk.document_id,
                "document_title": chunk.document_title,
                "chunk_text": chunk.chunk_text,
                "relevance_score": chunk.relevance_score,
                "chunk_index": chunk.chunk_index,
                "page_number": None,
            }
        )

    context = "\n\n---\n\n".join(parts)
    return context, sources
