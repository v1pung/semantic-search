from typing import Annotated

from fastapi import APIRouter, Depends

from src.dependencies import get_search_service
from src.schemas.search import SearchRequest, SearchResponse
from src.services.search_service import SearchService

router = APIRouter()


@router.post(
    "/search",
    response_model=SearchResponse,
    summary="Semantic search over Q&A pairs",
    description=(
        "Embeds the user query and retrieves the top-5 most similar questions "
        "from the vector database. Statistics (query text, timestamp, search "
        "duration) are persisted as part of the use case and do not affect "
        "response time on failure."
    ),
)
async def semantic_search(
    request: SearchRequest,
    search_service: Annotated[SearchService, Depends(get_search_service)],
) -> SearchResponse:
    results = await search_service.search(request.query, top_k=5)
    return SearchResponse(results=results)
