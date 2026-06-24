"""add metrics and timestamps to query_stats

Revision ID: 7e2b9f1a3c6d
Revises: 3f8a1c2d4e5b
Create Date: 2026-06-24 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "7e2b9f1a3c6d"
down_revision: str | None = "3f8a1c2d4e5b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Performance metrics
    op.add_column(
        "query_stats",
        sa.Column(
            "embed_duration_ms",
            sa.Float(),
            nullable=False,
            server_default="0.0",
        ),
    )

    # Result quality metrics
    op.add_column(
        "query_stats",
        sa.Column(
            "result_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "query_stats",
        sa.Column("top_score", sa.Float(), nullable=True),
    )

    # Request outcome
    op.add_column(
        "query_stats",
        sa.Column(
            "status",
            sa.String(32),
            nullable=False,
            server_default="ok",
        ),
    )
    op.add_column(
        "query_stats",
        sa.Column("error_message", sa.Text(), nullable=True),
    )

    # Audit timestamps — backfill from received_at for existing rows
    op.add_column(
        "query_stats",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.add_column(
        "query_stats",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # Backfill existing rows so audit timestamps match received_at
    op.execute(
        "UPDATE query_stats SET created_at = received_at, updated_at = received_at"
    )

    # Index for time-series queries and status filtering
    op.create_index("ix_query_stats_created_at", "query_stats", ["created_at"])
    op.create_index("ix_query_stats_status", "query_stats", ["status"])


def downgrade() -> None:
    op.drop_index("ix_query_stats_status", table_name="query_stats")
    op.drop_index("ix_query_stats_created_at", table_name="query_stats")
    op.drop_column("query_stats", "updated_at")
    op.drop_column("query_stats", "created_at")
    op.drop_column("query_stats", "error_message")
    op.drop_column("query_stats", "status")
    op.drop_column("query_stats", "top_score")
    op.drop_column("query_stats", "result_count")
    op.drop_column("query_stats", "embed_duration_ms")
