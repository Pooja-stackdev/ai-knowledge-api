from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies.query import get_query_service
from app.schemas.query import QueryRequest, QueryResponse, SourceResponse
from app.services.knowledge.query_service import QueryService

router = APIRouter(
    prefix="/query",
    tags=["Query"],
)


@router.post(
    "",
    response_model=QueryResponse,
)
async def query_knowledge_base(
    request: QueryRequest,
    service: Annotated[
        QueryService,
        Depends(get_query_service),
    ],
):
    result = service.query(
        query=request.query,
        top_k=request.top_k,
    )

    return QueryResponse(
        query=result.query,
        answer=result.answer,
        sources=[
            SourceResponse(
                document_id=source.document_id,
                chunk_id=source.chunk_id,
                page_number=source.page_number,
                content=source.content,
            )
            for source in result.sources
        ],
    )