MIN_RETRIEVAL_CONFIDENCE: float = 0.4
MIN_RESPONSE_CONFIDENCE: float = 0.5
MAX_HALLUCINATION_RISK: float = 0.7
TOP_K_CHUNKS: int = 5
CHUNK_OVERLAP_TOKENS: int = 50
MAX_CONTEXT_TOKENS: int = 3000
LLM_TEMPERATURE: float = 0.1
LLM_MAX_TOKENS: int = 1024
CEREBRAS_MODEL: str = "gpt-oss-120"
LOW_CONFIDENCE_FLAG_THRESHOLD: int = 3

FALLBACK_MESSAGE: str = (
    "I could not find reliable information in the approved company documents to answer your question. "
    "Please contact your administrator or check if the relevant documents have been uploaded and approved."
)

UNCERTAINTY_PHRASES: tuple[str, ...] = (
    "i'm not sure",
    "i don't know",
    "i cannot",
    "i can't",
    "unclear",
    "uncertain",
    "not certain",
    "might be",
    "possibly",
    "perhaps",
    "it seems",
    "it appears",
)
