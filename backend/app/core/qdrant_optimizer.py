"""
Qdrant collection optimisation helpers — HNSW tuning and payload indexes.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

HNSW_M: int = 16
HNSW_EF_CONSTRUCT: int = 100
VECTOR_DIMENSIONS: int = 384


@dataclass
class CollectionStats:
    collection_name: str
    vector_count: int
    status: str
    memory_usage_mb: float = 0.0


def optimize_collection_settings(client: Any, collection_name: str) -> bool:
    """Apply HNSW m=16, ef_construct=100 to an existing collection."""
    try:
        from qdrant_client.models import HnswConfigDiff, OptimizersConfigDiff
        client.update_collection(
            collection_name=collection_name,
            hnsw_config=HnswConfigDiff(m=HNSW_M, ef_construct=HNSW_EF_CONSTRUCT),
            optimizer_config=OptimizersConfigDiff(indexing_threshold=20000),
        )
        logger.info("Optimized HNSW settings for collection %s", collection_name)
        return True
    except Exception as exc:
        logger.warning("Could not optimize collection %s: %s", collection_name, exc)
        return False


def create_payload_indexes(client: Any, collection_name: str) -> bool:
    """Create payload indexes on organization_id and document_id for fast filtering."""
    try:
        from qdrant_client.models import PayloadSchemaType
        client.create_payload_index(
            collection_name=collection_name,
            field_name="organization_id",
            field_schema=PayloadSchemaType.KEYWORD,
        )
        client.create_payload_index(
            collection_name=collection_name,
            field_name="document_id",
            field_schema=PayloadSchemaType.KEYWORD,
        )
        logger.info("Created payload indexes for collection %s", collection_name)
        return True
    except Exception as exc:
        logger.warning("Could not create payload indexes for %s: %s", collection_name, exc)
        return False


def get_collection_stats(client: Any, collection_name: str) -> CollectionStats:
    """Return vector count, status, and estimated memory usage for a collection."""
    try:
        info = client.get_collection(collection_name)
        vector_count = getattr(info, "vectors_count", 0) or 0
        status = str(getattr(info, "status", "unknown"))
        # Rough memory estimate: 384 dims × 4 bytes × vectors
        memory_mb = round(vector_count * VECTOR_DIMENSIONS * 4 / 1_048_576, 2)
        return CollectionStats(
            collection_name=collection_name,
            vector_count=vector_count,
            status=status,
            memory_usage_mb=memory_mb,
        )
    except Exception as exc:
        logger.warning("Could not get stats for %s: %s", collection_name, exc)
        return CollectionStats(
            collection_name=collection_name,
            vector_count=0,
            status="unreachable",
        )
