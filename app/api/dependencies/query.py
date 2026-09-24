from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.connection import get_db_session
from app.database.repositories.document_chunk import (
    DocumentChunkRepository,
)
from app.rag.context_builder import ContextBuilder
from app.rag.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddingProvider,
)
from app.rag.llm.groq import GroqLLMProvider
from app.rag.prompt_builder import PromptBuilder
from app.rag.vectorstore.faiss_store import FaissVectorStore
from app.services.knowledge.embedding_service import EmbeddingService
from app.services.knowledge.query_service import QueryService
from app.services.knowledge.retrieval_service import RetrievalService
from app.services.knowledge.vector_service import VectorService


@lru_cache
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService(
        provider=SentenceTransformerEmbeddingProvider(
            model_name=settings.embedding_model,
        )
    )


@lru_cache
def get_vector_store() -> FaissVectorStore:
    return FaissVectorStore(
        dimension=settings.embedding_dimension,
        index_path=settings.faiss_index_path,
    )

@lru_cache
def get_vector_service() -> EmbeddingService:
    return VectorService(
        vector_store=get_vector_store()
    )


def get_retrieval_service(
    db: Annotated[Session, Depends(get_db_session)],
) -> RetrievalService:
    return RetrievalService(
        embedding_service=get_embedding_service(),
        vector_store=get_vector_store(),
        chunk_repository=DocumentChunkRepository(db),
    )


def get_query_service(
    retrieval_service: Annotated[
        RetrievalService,
        Depends(get_retrieval_service),
    ],
) -> QueryService:
    llm_provider = GroqLLMProvider(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
    )

    return QueryService(
        retrieval_service=retrieval_service,
        context_builder=ContextBuilder(),
        prompt_builder=PromptBuilder(),
        llm_provider=llm_provider,
    )