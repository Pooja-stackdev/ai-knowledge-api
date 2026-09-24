from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(
        min_length=1,
        max_length=2000,
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
    )
class SourceResponse(BaseModel):
    document_id: int
    chunk_id: int
    page_number: int
    content: str
    
class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: list[SourceResponse]