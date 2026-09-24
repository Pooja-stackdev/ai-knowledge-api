from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ContextSource:
    source_number: int
    document_id: int
    chunk_id: int
    page_number: int
    content: str


@dataclass(frozen=True, slots=True)
class RetrievalContext:
    text: str
    sources: list[ContextSource]