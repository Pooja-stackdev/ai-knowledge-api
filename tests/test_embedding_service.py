import pytest

from app.exceptions.common import BadRequestException
from app.services.knowledge.embedding_service import EmbeddingService


class FakeEmbeddingProvider:

    def embed_documents(
        self,
        texts,
    ):
        return [
            [0.1, 0.2, 0.3]
            for _ in texts
        ]


def test_embed_texts():
    service = EmbeddingService(
        provider=FakeEmbeddingProvider(),
    )

    embeddings = service.embed_texts(
        [
            "hello world",
            "another document",
        ],
    )

    assert len(embeddings) == 2
    assert len(embeddings[0]) == 3

class EmptyEmbeddingProvider:

    def embed_documents(self, texts):
        return []


def test_embed_query_raises_when_provider_returns_no_embedding():

    service = EmbeddingService(
        provider=EmptyEmbeddingProvider(),
    )

    with pytest.raises(
        BadRequestException,
        match="query.embedding_failed",
    ):
        service.embed_query(
            "What is the refund policy?"
        )