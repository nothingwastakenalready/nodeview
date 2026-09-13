"""store monitoring result details

Revision ID: 20260913_02
Revises: 20260913_01
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260913_02"
down_revision: str | None = "20260913_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    measurement_columns = {column["name"] for column in inspector.get_columns("measurements")}
    if "details_json" not in measurement_columns:
        op.add_column("measurements", sa.Column("details_json", sa.Text(), nullable=True))

    state_columns = {column["name"] for column in inspector.get_columns("check_states")}
    if "details_json" not in state_columns:
        op.add_column("check_states", sa.Column("details_json", sa.Text(), nullable=True))


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    state_columns = {column["name"] for column in inspector.get_columns("check_states")}
    if "details_json" in state_columns:
        op.drop_column("check_states", "details_json")

    measurement_columns = {column["name"] for column in inspector.get_columns("measurements")}
    if "details_json" in measurement_columns:
        op.drop_column("measurements", "details_json")
