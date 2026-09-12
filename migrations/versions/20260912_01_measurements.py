"""add measurement history

Revision ID: 20260912_01
Revises:
Create Date: 2026-09-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260912_01"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "measurements",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("service_name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_measurements_checked_at"),
        "measurements",
        ["checked_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_measurements_service_name"),
        "measurements",
        ["service_name"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_measurements_service_name"), table_name="measurements")
    op.drop_index(op.f("ix_measurements_checked_at"), table_name="measurements")
    op.drop_table("measurements")
