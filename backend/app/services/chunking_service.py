import hashlib
import re

from app.models.document import DocumentChunk


def get_token_count(text: str) -> int:
    return len(re.findall(r"\S+", text))


def calculate_chunk_hash(chunk_text: str) -> str:
    return hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [part.strip() for part in parts if part.strip()]


def semantic_chunk(text: str, target_min: int = 300, target_max: int = 500, overlap_tokens: int = 50) -> list[dict]:
    sentences = _sentences(text)
    chunks: list[dict] = []
    current: list[str] = []
    for sentence in sentences:
        candidate = " ".join(current + [sentence])
        if current and get_token_count(candidate) > target_max:
            chunk_text = " ".join(current)
            chunks.append({"chunk_text": chunk_text, "token_count": get_token_count(chunk_text)})
            overlap = chunk_text.split()[-overlap_tokens:]
            current = [" ".join(overlap), sentence]
        else:
            current.append(sentence)
    if current:
        chunk_text = " ".join(current)
        chunks.append({"chunk_text": chunk_text, "token_count": get_token_count(chunk_text)})
    return chunks


def hierarchical_chunk(structured_text: dict) -> list[dict]:
    chunks = []
    for section_index, section in enumerate(structured_text.get("sections", [])):
        for paragraph_index, paragraph in enumerate(section.get("paragraphs", [])):
            chunks.append(
                {
                    "heading": section.get("heading"),
                    "level": 3,
                    "section_index": section_index,
                    "paragraph_index": paragraph_index,
                    "chunk_text": paragraph,
                    "token_count": get_token_count(paragraph),
                }
            )
    return chunks


def hybrid_chunk(structured_text: dict | str) -> list[dict]:
    if isinstance(structured_text, str):
        structured_text = {"sections": [{"heading": "Document", "paragraphs": [structured_text]}]}
    output = []
    for section in structured_text.get("sections", []):
        section_text = "\n".join(section.get("paragraphs", []))
        for chunk in semantic_chunk(section_text):
            chunk["heading"] = section.get("heading")
            chunk["chunk_hash"] = calculate_chunk_hash(chunk["chunk_text"])
            output.append(chunk)
    return output


async def save_chunks_to_db(db, document, chunks: list[dict]) -> list[DocumentChunk]:
    saved = []
    for index, chunk in enumerate(chunks):
        row = DocumentChunk(
            document_id=document.id,
            organization_id=document.organization_id,
            chunk_index=index,
            chunk_text=chunk["chunk_text"],
            chunk_hash=chunk.get("chunk_hash") or calculate_chunk_hash(chunk["chunk_text"]),
            token_count=chunk.get("token_count") or get_token_count(chunk["chunk_text"]),
            embedding_status="pending",
        )
        db.add(row)
        saved.append(row)
    await db.flush()
    return saved
