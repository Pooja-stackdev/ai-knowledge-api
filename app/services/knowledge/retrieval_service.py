import logging

from app.core.config import settings
from app.database.repositories.document_chunk import (
    DocumentChunkRepository,
)
from app.rag.result import RetrievedChunk
from app.rag.vectorstore.base import VectorStore
from app.services.knowledge.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class RetrievalService:
    """Retrieve document chunks relevant to a user query."""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
        chunk_repository: DocumentChunkRepository,
        score_threshold: float | None = None,
    ) -> None:
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.chunk_repository = chunk_repository
        self.score_threshold = (
            settings.retrieval_score_threshold
            if score_threshold is None
            else score_threshold
        )

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        """Find the most relevant document chunks for a query."""

        query_embedding = self.embedding_service.embed_query(query)

        matches = self.vector_store.search(
            embedding=query_embedding,
            top_k=top_k,
        )

        logger.info( 
            "Vector retrieval completed | query=%r | top_k=%d | results=%d", 
            query, 
            top_k, 
            len(matches), 
        ) 

        logger.info( 
            "Vector similarity scores | %s", 
            [ { "chunk_id": chunk_id, "score": score, } for chunk_id, score in matches ], 
        )

        if not matches:
            return []

        # IndexFlatIP returns similarity scores. 
        filtered_matches = [ 
            (chunk_id, score) 
            for chunk_id, score in matches 
            if ( self.score_threshold is None or score >= self.score_threshold ) 
        ]

        logger.info( 
            "Retrieval threshold filtering | threshold=%s | before=%d | after=%d", 
            self.score_threshold, 
            len(matches), 
            len(filtered_matches), 
        ) 

        if not filtered_matches: 
            logger.info( "No relevant chunks found for query" ) 
            return []

        chunk_ids = [ 
            chunk_id 
            for chunk_id, _ in filtered_matches 
        ]

        chunks = self.chunk_repository.get_by_ids(chunk_ids)

        chunks_by_id = {
            chunk.id: chunk
            for chunk in chunks
        }

        results: list[RetrievedChunk] = []
        seen_contents: set[str] = set()

        for chunk_id, score in filtered_matches:
            chunk = chunks_by_id.get(chunk_id)

            if chunk is None:
                logger.warning( "FAISS returned chunk that was not found in database | " "chunk_id=%s", chunk_id, )
                continue

            content_key = chunk.content.strip()

            if content_key in seen_contents: 
                logger.info( "Skipping duplicate chunk | chunk_id=%s", chunk.id, ) 
                continue 

            seen_contents.add(content_key)

            results.append(
                RetrievedChunk(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    content=chunk.content,
                    page_number=chunk.page_number,
                    chunk_index=chunk.chunk_index,
                    score=score,
                )
            )

            logger.info( "Retrieved relevant chunks | count=%d", len(results), )

        return results