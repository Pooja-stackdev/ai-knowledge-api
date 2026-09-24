from collections.abc import Sequence
from typing import Protocol


class EmbeddingProvider(Protocol):
    """Interface for generating text embeddings."""

    def embed_documents(
        self,
        texts: Sequence[str],
    ) -> list[list[float]]:
        """Generate embeddings for multiple text inputs."""
        ...