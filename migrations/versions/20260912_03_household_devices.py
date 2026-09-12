"""add workspace-owned household devices and connector metadata

Revision ID: 20260912_03
Revises: 20260912_02
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260912_03"
down_revision: str | None = "20260912_02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "devices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("workspace_id", sa.Integer(), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("connector", sa.String(32), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("endpoint", sa.String(512), nullable=True),
        sa.Column("credential_ref", sa.String(256), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_devices_workspace_id", "devices", ["workspace_id"])
    op.create_index("ix_devices_connector", "devices", ["connector"])


def downgrade() -> None:
    op.drop_index("ix_devices_connector", table_name="devices")
    op.drop_index("ix_devices_workspace_id", table_name="devices")
    op.drop_table("devices")
