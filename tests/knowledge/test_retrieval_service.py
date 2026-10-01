from app.rag.result import RetrievedChunk
from app.services.knowledge.retrieval_service import RetrievalService


class FakeEmbeddingService:

    def embed_query(
        self,
        query: str,
    ) -> list[float]:
        return [0.1, 0.2, 0.3]


class FakeVectorStore:

    def __init__(
        self,
        matches: list[tuple[int, float]],
    ):
        self.matches = matches
        self.search_calls = []

    def search(
        self,
        embedding,
        top_k: int = 5,
        allowed_ids=None,
    ) -> list[tuple[int, float]]:
        self.search_calls.append(
            {
                "embedding": embedding,
                "top_k": top_k,
                "allowed_ids": allowed_ids,
            }
        )

        return self.matches


class FakeChunk:

    def __init__(
        self,
        *,
        chunk_id: int,
        document_id: int,
        content: str,
        page_number: int,
        chunk_index: int,
    ):
        self.id = chunk_id
        self.document_id = document_id
        self.content = content
        self.page_number = page_number
        self.chunk_index = chunk_index


class FakeChunkRepository:

    def __init__(
        self,
        chunks,
    ):
        self.chunks = chunks
        self.requested_ids = []

    def get_by_ids(
        self,
        chunk_ids,
    ):
        self.requested_ids.append(list(chunk_ids))

        return [
            chunk
            for chunk in self.chunks
            if chunk.id in chunk_ids
        ]

    def get_ids_by_document_ids(
        self,
        document_ids,
    ):
        return [
            chunk.id
            for chunk in self.chunks
            if chunk.document_id in document_ids
        ]


class FakeDocumentRepository:

    def __init__(
        self,
        accessible_document_ids=None,
    ):
        self.accessible_document_ids = (
            accessible_document_ids
            if accessible_document_ids is not None
            else [1, 2, 3]
        )
        self.requested_role_ids = []

    def get_accessible_document_ids(
        self,
        role_ids,
    ):
        self.requested_role_ids.append(list(role_ids))

        return self.accessible_document_ids


def create_service(
    *,
    matches,
    chunks,
    score_threshold=0.8,
    accessible_document_ids=None,
):
    return RetrievalService(
        embedding_service=FakeEmbeddingService(),
        vector_store=FakeVectorStore(matches),
        chunk_repository=FakeChunkRepository(chunks),
        document_repository=FakeDocumentRepository(
            accessible_document_ids
        ),
        score_threshold=score_threshold,
    )


def test_retrieve_returns_relevant_chunks():
    chunks = [
        FakeChunk(
            chunk_id=10,
            document_id=1,
            content="Refunds are available within 30 days.",
            page_number=4,
            chunk_index=0,
        ),
    ]

    service = create_service(
        matches=[
            (10, 0.91),
        ],
        chunks=chunks,
    )

    results = service.retrieve(
        query="What is the refund policy?",
        role_ids=[],
    )

    assert len(results) == 1

    result = results[0]

    assert isinstance(result, RetrievedChunk)
    assert result.chunk_id == 10
    assert result.document_id == 1
    assert result.page_number == 4
    assert result.chunk_index == 0
    assert result.content == (
        "Refunds are available within 30 days."
    )
    assert result.score == 0.91


def test_retrieve_filters_results_below_score_threshold():
    chunks = [
        FakeChunk(
            chunk_id=10,
            document_id=1,
            content="Relevant refund information.",
            page_number=4,
            chunk_index=0,
        ),
        FakeChunk(
            chunk_id=20,
            document_id=1,
            content="Irrelevant information.",
            page_number=5,
            chunk_index=1,
        ),
    ]

    service = create_service(
        matches=[
            (10, 0.91),
            (20, 0.72),
        ],
        chunks=chunks,
        score_threshold=0.80,
    )

    results = service.retrieve(
        query="What is the refund policy?",
        role_ids=[],
    )

    assert len(results) == 1
    assert results[0].chunk_id == 10
    assert results[0].score == 0.91


def test_retrieve_returns_empty_when_all_results_are_below_threshold():
    chunks = [
        FakeChunk(
            chunk_id=10,
            document_id=1,
            content="Some information.",
            page_number=1,
            chunk_index=0,
        ),
    ]

    vector_store = FakeVectorStore(
        matches=[
            (10, 0.50),
        ],
    )

    chunk_repository = FakeChunkRepository(chunks)

    service = RetrievalService(
        embedding_service=FakeEmbeddingService(),
        vector_store=vector_store,
        chunk_repository=chunk_repository,
        document_repository=FakeDocumentRepository(),
        score_threshold=0.80,
    )

    results = service.retrieve(
        query="Some question?",
        role_ids=[],
    )

    assert results == []

    assert chunk_repository.requested_ids == []


def test_retrieve_skips_chunk_missing_from_database():
    chunks = []

    service = create_service(
        matches=[
            (999, 0.95),
        ],
        chunks=chunks,
    )

    results = service.retrieve(
        query="What information is available?",
        role_ids=[],
    )

    assert results == []


def test_retrieve_removes_duplicate_content():
    chunks = [
        FakeChunk(
            chunk_id=10,
            document_id=1,
            content="Refunds are available within 30 days.",
            page_number=4,
            chunk_index=0,
        ),
        FakeChunk(
            chunk_id=20,
            document_id=1,
            content="Refunds are available within 30 days.",
            page_number=5,
            chunk_index=1,
        ),
    ]

    service = create_service(
        matches=[
            (10, 0.95),
            (20, 0.90),
        ],
        chunks=chunks,
    )

    results = service.retrieve(
        query="What is the refund policy?",
        role_ids=[],
    )

    assert len(results) == 1
    assert results[0].chunk_id == 10
    assert results[0].score == 0.95


def test_retrieve_preserves_vector_store_order():
    chunks = [
        FakeChunk(
            chunk_id=10,
            document_id=1,
            content="First result.",
            page_number=2,
            chunk_index=0,
        ),
        FakeChunk(
            chunk_id=20,
            document_id=2,
            content="Second result.",
            page_number=7,
            chunk_index=0,
        ),
    ]

    service = create_service(
        matches=[
            (20, 0.95),
            (10, 0.90),
        ],
        chunks=chunks,
    )

    results = service.retrieve(
        query="test",
        role_ids=[],
    )

    assert [result.chunk_id for result in results] == [
        20,
        10,
    ]

    assert [result.score for result in results] == [
        0.95,
        0.90,
    ]