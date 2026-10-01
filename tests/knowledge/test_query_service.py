import pytest

from app.rag.context_builder import ContextBuilder
from app.rag.prompt_builder import PromptBuilder
from app.rag.result import RetrievedChunk
from app.services.knowledge.query_service import QueryService
from tests.fakes.fake_llm import FakeLLMProvider


class FakeRetrievalService:

    def __init__(self, chunks):
        self.chunks = chunks

    def retrieve(
        self,
        query: str,
        role_ids:list[int],
        top_k: int = 5,
    ):
        return self.chunks

def test_query_rejects_whitespace_only(client,access_token):
    response = client.post(
        "/query",
        json={"query": "   "},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 422

def test_query_rejects_query_over_max_length(client,access_token):
    response = client.post(
        "/query",
        json={"query": "a" * 2001},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 422

def test_query_returns_answer_and_sources():
    chunks = [
        RetrievedChunk(
            chunk_id=10,
            document_id=1,
            content="Refunds are available within 30 days.",
            page_number=4,
            chunk_index=0,
            score=0.91,
        ),
    ]

    retrieval_service = FakeRetrievalService(chunks)
    llm_provider = FakeLLMProvider(
        response="Customers can request refunds within 30 days."
    )

    service = QueryService(
        retrieval_service=retrieval_service,
        context_builder=ContextBuilder(),
        prompt_builder=PromptBuilder(),
        llm_provider=llm_provider,
    )

    result = service.query(
        query="How long do I have to request a refund?",
        role_ids=[1]
    )

    assert result.answer == (
        "Customers can request refunds within 30 days."
    )

    assert len(result.sources) == 1
    assert result.sources[0].document_id == 1
    assert result.sources[0].page_number == 4


def test_query_sends_context_to_llm():
    chunks = [
        RetrievedChunk(
            chunk_id=10,
            document_id=1,
            content="Refunds are available within 30 days.",
            page_number=4,
            chunk_index=0,
            score=0.91,
        ),
    ]

    retrieval_service = FakeRetrievalService(chunks)
    llm_provider = FakeLLMProvider()

    service = QueryService(
        retrieval_service=retrieval_service,
        context_builder=ContextBuilder(),
        prompt_builder=PromptBuilder(),
        llm_provider=llm_provider,
    )

    service.query(
        query="How long do I have to request a refund?",
        role_ids=[1]
    )

    assert len(llm_provider.calls) == 1

    user_prompt = llm_provider.calls[0]["user_prompt"]

    assert "Refunds are available within 30 days." in user_prompt
    assert "How long do I have to request a refund?" in user_prompt


def test_query_does_not_call_llm_when_no_context():
    retrieval_service = FakeRetrievalService([])
    llm_provider = FakeLLMProvider()

    service = QueryService(
        retrieval_service=retrieval_service,
        context_builder=ContextBuilder(),
        prompt_builder=PromptBuilder(),
        llm_provider=llm_provider,
    )

    result = service.query(
        query="What is the refund policy?",
        role_ids=[1]
    )

    assert result.sources == []

    assert result.answer == (
        "I couldn't find relevant information in the knowledge base."
    )

    assert len(llm_provider.calls) == 0

def test_query_returns_multiple_sources():
    chunks = [
        RetrievedChunk(
            chunk_id=10,
            document_id=1,
            content="Refunds are available within 30 days.",
            page_number=4,
            chunk_index=0,
            score=0.91,
        ),
        RetrievedChunk(
            chunk_id=20,
            document_id=2,
            content="Refund requests require proof of purchase.",
            page_number=2,
            chunk_index=1,
            score=0.87,
        ),
    ]

    retrieval_service = FakeRetrievalService(chunks)
    llm_provider = FakeLLMProvider()

    service = QueryService(
        retrieval_service=retrieval_service,
        context_builder=ContextBuilder(),
        prompt_builder=PromptBuilder(),
        llm_provider=llm_provider,
    )

    result = service.query(
        query="What is the refund policy?",
        role_ids=[1]
    )

    assert len(result.sources) == 2

    assert result.sources[0].document_id == 1
    assert result.sources[0].page_number == 4

    assert result.sources[1].document_id == 2
    assert result.sources[1].page_number == 2





def test_query_rejects_empty_query():
    retrieval_service = FakeRetrievalService([])
    llm_provider = FakeLLMProvider()

    service = QueryService(
        retrieval_service=retrieval_service,
        context_builder=ContextBuilder(),
        prompt_builder=PromptBuilder(),
        llm_provider=llm_provider,
    )

    with pytest.raises(ValueError, match="Query cannot be empty"):
        service.query(
            query="   ",
            role_ids=[1],
        )

    assert len(llm_provider.calls) == 0