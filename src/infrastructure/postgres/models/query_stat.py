from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.postgres.base import Base


class QueryStat(Base):
    __tablename__ = "query_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # --- core request data ---
    user_query: Mapped[str] = mapped_column(String, nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # --- performance metrics ---
    search_duration_ms: Mapped[float] = mapped_column(Float, nullable=False)
    embed_duration_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # --- result quality metrics ---
    result_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    top_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # --- request outcome ---
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="ok"
    )  # "ok" | "error"
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- audit timestamps ---
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
