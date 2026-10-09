from app.core.i18n import get_message
from app.exceptions.common import BadRequestException,ValidationException
from app.rag.context_builder import ContextBuilder
from app.rag.llm.base import LLMProvider
from app.rag.prompt_builder import PromptBuilder
from app.rag.result import QueryResult
from app.services.knowledge.retrieval_service import RetrievalService


class QueryService:
    """Orchestrate retrieval, context building, and LLM generation."""

    def __init__(
        self,
        retrieval_service: RetrievalService,
        context_builder: ContextBuilder,
        prompt_builder: PromptBuilder,
        llm_provider: LLMProvider,
    ) -> None:
        self.retrieval_service = retrieval_service
        self.context_builder = context_builder
        self.prompt_builder = prompt_builder
        self.llm_provider = llm_provider

    def query(
        self,
        *,
        query: str,
        role_ids: list[int],
        top_k: int = 5,
    ) -> QueryResult:
        """Answer a query using retrieved knowledge and an LLM."""

        if not query.strip():
            raise ValidationException("query.empty")
    
        chunks = self.retrieval_service.retrieve(
            query=query,
            role_ids=role_ids,
            top_k=top_k,
        )

        context = self.context_builder.build(chunks)

        if not context.text.strip():
            return QueryResult(
                query=query,
                answer=get_message("query.no_relevant_info"),
                sources=[],
            )

        system_prompt, user_prompt = self.prompt_builder.build(
            query=query,
            context=context,
        )

        answer = self.llm_provider.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        return QueryResult(
            query=query,
            answer=answer,
            sources=context.sources,
        )
