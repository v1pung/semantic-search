# Import all ORM models here so that Alembic's env.py can register them
# on Base.metadata with a single import of this package.
from src.infrastructure.postgres.models.query_stat import QueryStat  # noqa: F401
