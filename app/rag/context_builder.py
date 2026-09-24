from collections.abc import Sequence

from app.rag.context import ContextSource, RetrievalContext
from app.rag.result import RetrievedChunk


class ContextBuilder:

    def __init__(self, max_characters: int = 12_000) -> None:
        self.max_characters = max_characters

    def build(
        self,
        chunks: Sequence[RetrievedChunk],
    ) -> RetrievalContext:
        if not chunks:
            return RetrievalContext(
                text="",
                sources=[],
            )

        context_parts: list[str] = []
        sources: list[ContextSource] = []
        total_characters = 0

        for index, chunk in enumerate(chunks, start=1):
            source_text = (
                f"[Source {index}]\n"
                f"Document ID: {chunk.document_id}\n"
                f"Page: {chunk.page_number}\n"
                f"Content:\n{chunk.content}"
            )

            if total_characters + len(source_text) > self.max_characters:
                break

            context_parts.append(source_text)

            sources.append(
                ContextSource(
                    source_number=index,
                    document_id=chunk.document_id,
                    chunk_id=chunk.chunk_id,
                    page_number=chunk.page_number,
                    content=chunk.content,
                )
            )

            total_characters += len(source_text)

        return RetrievalContext(
            text="\n\n".join(context_parts),
            sources=sources,
        )