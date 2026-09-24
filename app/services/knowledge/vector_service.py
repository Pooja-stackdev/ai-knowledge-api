from collections.abc import Sequence

from app.rag.vectorstore.base import VectorStore


class VectorService:
    """Manage vector storage operations for document embeddings."""

    def __init__(
        self,
        vector_store: VectorStore,
    ) -> None:
        self.vector_store = vector_store

    def add_embeddings(
        self,
        *,
        chunk_ids: Sequence[int],
        embeddings: Sequence[Sequence[float]],
    ) -> None:
        """Store embeddings mapped to their document chunk IDs."""
        if len(chunk_ids) != len(embeddings):
            raise ValueError(
                "Chunk ID count must match embedding count"
            )

        self.vector_store.add(
            ids=chunk_ids,
            embeddings=embeddings,
        )

    def search(
        self,
        embedding: Sequence[float],
        top_k: int = 5,
    ) -> list[tuple[int, float]]:
        """Search the vector store for the nearest matching chunks."""
        return self.vector_store.search(
            embedding=embedding,
            top_k=top_k,
        )

    def delete_embeddings(
        self,
        chunk_ids: Sequence[int],
    ) -> None:
        """Delete embeddings associated with the given chunk IDs."""
        if not chunk_ids:
            return

        self.vector_store.delete(chunk_ids)