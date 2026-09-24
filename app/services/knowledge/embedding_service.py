from collections.abc import Sequence

from app.rag.embeddings.base import EmbeddingProvider


class EmbeddingService:
    """Generate vector embeddings for documents and queries."""

    def __init__(
        self,
        provider: EmbeddingProvider,
    ) -> None:
        self.provider = provider

    def embed_texts(
        self,
        texts: Sequence[str],
    ) -> list[list[float]]:
        """Generate embeddings for multiple text inputs."""
        if not texts:
            return []

        return self.provider.embed_documents(texts)

    def embed_query(
        self,
        query: str,
    ) -> list[float]:
        """Generate an embedding for a single search query."""
        if not query.strip():
            raise ValueError("Query cannot be empty")

        embeddings = self.provider.embed_documents([query])

        if not embeddings:
            raise ValueError("Failed to generate query embedding")

        return embeddings[0]