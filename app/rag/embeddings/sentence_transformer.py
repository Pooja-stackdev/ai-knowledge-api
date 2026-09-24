from collections.abc import Sequence

from sentence_transformers import SentenceTransformer


class SentenceTransformerEmbeddingProvider:

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
    ) -> None:
        self.model = SentenceTransformer(
            model_name,
        )

    def embed_documents(
        self,
        texts: Sequence[str],
    ) -> list[list[float]]:
        """Generate normalized embeddings for the given texts."""
        if not texts:
            return []

        embeddings = self.model.encode(
            list(texts),
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        return embeddings.tolist()