import logging
from collections.abc import Sequence

from app.exceptions.base import AppException
from app.exceptions.common import BadRequestException
from app.rag.embeddings.base import EmbeddingProvider

logger = logging.getLogger(__name__)

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
            logger.info( 
                f"Query Empty:{query}", 
            ) 
            raise BadRequestException("query.empty")

        embeddings = self.provider.embed_documents([query])

        logger.info( 
            f"embeddings length:{len(embeddings)}" 
        ) 
        
        if not embeddings:
            logger.info("Failed to generate query embedding") 
            raise BadRequestException("query.embedding_failed")

        return embeddings[0]