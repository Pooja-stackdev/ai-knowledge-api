from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies.authorization import (
    get_current_user_role_ids,
    require_permission,
)
from app.api.dependencies.query import get_query_service
from app.database.models.user import User
from app.schemas.query import QueryRequest, QueryResponse, SourceResponse
from app.services.knowledge.query_service import QueryService

router = APIRouter(
    prefix="/query",
    tags=["Query"],
)

QueryServiceDep = Annotated[
    QueryService,
    Depends(get_query_service),
]

CurrentUserDep = Annotated[
    User,
    Depends(require_permission("query.execute")),
]


@router.post(
    "",
    response_model=QueryResponse,
)
async def query_knowledge_base(
    request: QueryRequest,
    service: QueryServiceDep,
    # current_user: CurrentUserDep,
    role_ids: Annotated[
        list[int],
        Depends(get_current_user_role_ids),
    ],
) -> QueryResponse:
    """Execute a knowledge-base query for an authorized user."""
    result = service.query(
        query=request.query,
        top_k=request.top_k,
        role_ids=role_ids,
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