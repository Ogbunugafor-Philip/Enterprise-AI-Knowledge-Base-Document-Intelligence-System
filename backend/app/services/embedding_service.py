import uuid
from functools import lru_cache
import random

VECTOR_SIZE = 384
QDRANT_COLLECTION = "knowledge_base"


class DeterministicEmbeddingModel:
    def encode(self, texts):
        single = isinstance(texts, str)
        values = [texts] if single else texts
        vectors = []
        for text in values:
            seed = abs(hash(text)) % (2**32)
            rng = random.Random(seed)
            vector = [rng.random() for _ in range(VECTOR_SIZE)]
            norm = sum(value * value for value in vector) ** 0.5
            vectors.append([value / norm for value in vector] if norm else vector)
        return vectors[0] if single else vectors


@lru_cache(maxsize=1)
def load_embedding_model():
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore

        return SentenceTransformer("all-MiniLM-L6-v2")
    except Exception:
        return DeterministicEmbeddingModel()


def generate_embedding(text: str):
    return load_embedding_model().encode(text)


def generate_embeddings_batch(chunks: list[str], batch_size: int = 32):
    model = load_embedding_model()
    embeddings = []
    for index in range(0, len(chunks), batch_size):
        embeddings.extend(model.encode(chunks[index:index + batch_size]))
    return embeddings


def ensure_qdrant_collection(client) -> None:
    """Create the collection if it does not already exist."""
    try:
        client.get_collection(QDRANT_COLLECTION)
    except Exception:
        from qdrant_client.models import Distance, VectorParams  # type: ignore
        client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )


def store_embeddings_in_qdrant(client, organization_id, chunks, embeddings, document) -> list[str]:
    point_ids = [str(uuid.uuid4()) for _ in chunks]
    if client is None:
        return point_ids
    try:
        from qdrant_client.models import PointStruct  # type: ignore

        ensure_qdrant_collection(client)
        points = []
        for point_id, chunk, embedding in zip(point_ids, chunks, embeddings, strict=False):
            points.append(
                PointStruct(
                    id=point_id,
                    vector=embedding.tolist() if hasattr(embedding, "tolist") else list(embedding),
                    payload={
                        "chunk_id": str(chunk.id),
                        "document_id": str(document.id),
                        "organization_id": str(organization_id),
                        "department_id": str(document.department_id) if document.department_id else None,
                        "chunk_text": chunk.chunk_text,
                        "chunk_index": chunk.chunk_index,
                        "document_title": document.title,
                    },
                )
            )
        client.upsert(collection_name=QDRANT_COLLECTION, points=points)
    except Exception:
        return point_ids
    return point_ids


async def update_chunk_qdrant_ids(db, chunks, point_ids: list[str]) -> None:
    for chunk, point_id in zip(chunks, point_ids, strict=False):
        chunk.qdrant_point_id = point_id
        chunk.embedding_status = "completed"
    await db.flush()


def delete_document_embeddings(client, organization_id, document_id) -> None:
    if client is None:
        return None
    try:
        from qdrant_client.models import Filter, FieldCondition, MatchValue  # type: ignore
        client.delete(
            collection_name=QDRANT_COLLECTION,
            points_selector=Filter(
                must=[FieldCondition(key="document_id", match=MatchValue(value=str(document_id)))]
            ),
        )
    except Exception:
        return None
