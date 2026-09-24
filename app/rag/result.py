from dataclasses import dataclass

from app.rag.context import ContextSource


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    chunk_id: int
    document_id: int
    content: str
    page_number: int
    chunk_index: int
    score: float




@dataclass(frozen=True, slots=True)
class QueryResult:
    query: str
    answer: str
    sources: list[ContextSource]