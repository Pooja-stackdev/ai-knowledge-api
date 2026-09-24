from app.rag.context_builder import ContextBuilder
from app.rag.result import RetrievedChunk


def test_build_context():

    chunks = [
        RetrievedChunk(
            chunk_id=10,
            document_id=1,
            content="Refunds are available.",
            page_number=4,
            chunk_index=2,
            score=0.91,
        ),
        RetrievedChunk(
            chunk_id=11,
            document_id=1,
            content="Refunds must be requested within 30 days.",
            page_number=5,
            chunk_index=3,
            score=0.87,
        ),
    ]

    builder = ContextBuilder()

    context = builder.build(
        chunks,
    )

    assert "[Source 1]" in context.text
    assert "[Source 2]" in context.text
    assert "Page: 4" in context.text
    assert "Page: 5" in context.text

    assert len(context.sources) == 2


def test_context_respects_character_limit():

    chunks = [
        RetrievedChunk(
            chunk_id=1,
            document_id=1,
            content="A" * 100,
            page_number=1,
            chunk_index=0,
            score=0.9,
        ),
        RetrievedChunk(
            chunk_id=2,
            document_id=1,
            content="B" * 100,
            page_number=2,
            chunk_index=1,
            score=0.8,
        ),
    ]

    builder = ContextBuilder(
        max_characters=150,
    )

    context = builder.build(
        chunks,
    )

    assert len(context.sources) == 1



