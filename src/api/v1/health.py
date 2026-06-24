"""
Health-check endpoints.

GET /health/live    — liveness probe: returns 200 if the process is running.
GET /health/ready   — readiness probe: checks Qdrant and Postgres connectivity.
"""

import logging
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_qdrant_client
from src.core.config import Settings, get_settings
from src.infrastructure.postgres.base import get_db

router = APIRouter(prefix="/health", tags=["health"])
logger = logging.getLogger(__name__)


@router.get(
    "/live",
    summary="Liveness probe",
    description="Returns 200 if the application process is running.",
)
async def liveness() -> dict:
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get(
    "/ready",
    summary="Readiness probe",
    description=(
        "Checks that all downstream dependencies (Qdrant, PostgreSQL) are reachable. "
        "Returns 200 if all checks pass, 503 otherwise."
    ),
)
async def readiness(
    settings: Annotated[Settings, Depends(get_settings)],
    qdrant_client=Depends(get_qdrant_client),
) -> JSONResponse:
    checks: dict[str, str] = {}
    ready = True

    # --- Qdrant check ---
    try:
        await qdrant_client.get_collections()
        checks["qdrant"] = "ok"
    except Exception as exc:
        logger.warning("Readiness: Qdrant check failed: %s", exc)
        checks["qdrant"] = "unavailable"
        ready = False

    # --- PostgreSQL check ---
    try:
        async for session in get_db(settings.POSTGRES_URL):
            await session.execute(text("SELECT 1"))
            checks["postgres"] = "ok"
            break
    except Exception as exc:
        logger.warning("Readiness: PostgreSQL check failed: %s", exc)
        checks["postgres"] = "unavailable"
        ready = False

    http_status = status.HTTP_200_OK if ready else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(
        status_code=http_status,
        content={
            "status": "ready" if ready else "not_ready",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": checks,
        },
    )
