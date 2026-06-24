"""
Rate-limiting setup using slowapi (wraps the `limits` library).

A single Limiter instance is created at import time and reused across the
application. The storage URI is read from Settings lazily so the module can
be imported before environment variables are fully resolved.

The limiter is keyed by client IP (X-Forwarded-For → REMOTE_ADDR fallback)
and backed by Redis so limits survive worker restarts and work correctly
with multiple uvicorn workers.

Attach to the app in create_app():

    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

Decorate endpoints with:

    @router.post("/search")
    @limiter.limit(get_settings().RATE_LIMIT_SEARCH)
    async def endpoint(request: Request, ...):   # `request` must be present
        ...

slowapi's SlowAPIMiddleware reads the limit from the decorated function and
enforces it using the limiter attached to app.state.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from src.core.config import get_settings

# Module-level singleton — created once at import time.
# Settings (and therefore the Redis URL) are resolved here.
limiter: Limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=get_settings().REDIS_RATE_LIMIT_URL,
    # Emit X-RateLimit-Limit / X-RateLimit-Remaining / X-RateLimit-Reset headers
    headers_enabled=True,
)
