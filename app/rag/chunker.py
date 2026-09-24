from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.database.models.document_chunk import DocumentChunk
from app.domain.models.document_content import LoadedDocument


class DocumentChunker:
    """Split loaded document pages into overlapping text chunks."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> None:
        if chunk_size <= 0:
            raise ValueError(
                "chunk_size must be greater than zero"
            )

        if chunk_overlap < 0:
            raise ValueError(
                "chunk_overlap cannot be negative"
            )

        if chunk_overlap >= chunk_size:
            raise ValueError(
                "chunk_overlap must be smaller than chunk_size"
            )

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=[
                "\n\n",
                "\n",
                ". ",
                " ",
                "",
            ],
        )

    def chunk(
        self,
        document: LoadedDocument,
    ) -> list[DocumentChunk]:
        """Split document pages into ordered database chunk objects."""
        chunks: list[DocumentChunk] = []
        chunk_index = 0

        for page in document.pages:
            page_chunks = self.splitter.split_text(
                page.text,
            )

            for text in page_chunks:
                chunks.append(
                    DocumentChunk(
                        content=text,
                        page_number=page.page_number,
                        chunk_index=chunk_index,
                    )
                )

                chunk_index += 1

        return chunks