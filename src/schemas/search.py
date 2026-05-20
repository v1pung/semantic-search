from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(
        ..., min_length=1, max_length=1000, description="User search query"
    )


class SearchResult(BaseModel):
    question: str
    answer: str
    score: float = Field(..., description="Cosine similarity score [0, 1]")


class SearchResponse(BaseModel):
    results: list[SearchResult]
