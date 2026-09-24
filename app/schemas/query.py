from pydantic import BaseModel, Field, field_validator


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

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Query cannot be empty")

        return value
class SourceResponse(BaseModel):
    document_id: int
    chunk_id: int
    page_number: int
    content: str
    
class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: list[SourceResponse]