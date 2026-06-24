from fastapi import APIRouter

from src.api.v1 import health, ingest, search, tasks

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(ingest.router, tags=["ingestion"])
api_router.include_router(search.router, tags=["search"])
api_router.include_router(tasks.router)
