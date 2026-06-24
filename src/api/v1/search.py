from time import perf_counter
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
        "Embeds the user query and retrieves the top-k most similar questions "
        "from the vector database. The response includes timing metrics and "
        "result count. Statistics (query text, timestamp, durations, scores) "
        "are persisted as part of the use case and do not affect response on failure."
    ),
)
async def semantic_search(
    request: SearchRequest,
    search_service: Annotated[SearchService, Depends(get_search_service)],
) -> SearchResponse:
    t0 = perf_counter()
    results = await search_service.search(request.query, top_k=5)
    search_duration_ms = (perf_counter() - t0) * 1000
    return SearchResponse(
        results=results,
        total_results=len(results),
        search_duration_ms=round(search_duration_ms, 3),
    )
