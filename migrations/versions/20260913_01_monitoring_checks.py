"""add workspace-owned monitoring checks

Revision ID: 20260913_01
Revises: 20260912_05
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260913_01"
down_revision: str | None = "20260912_05"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    measurement_columns = {column["name"] for column in inspector.get_columns("measurements")}
    for name in ("workspace_id", "device_id", "check_id"):
        if name not in measurement_columns:
            op.add_column("measurements", sa.Column(name, sa.Integer(), nullable=True))
            op.create_index(f"ix_measurements_{name}", "measurements", [name])

    op.create_table(
        "checks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("workspace_id", sa.Integer(), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("device_id", sa.Integer(), sa.ForeignKey("devices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("type", sa.String(16), nullable=False),
        sa.Column("url", sa.String(1024), nullable=True),
        sa.Column("host", sa.String(255), nullable=True),
        sa.Column("port", sa.Integer(), nullable=True),
        sa.Column("interval", sa.Float(), nullable=False, server_default="30"),
        sa.Column("timeout", sa.Float(), nullable=False, server_default="2"),
        sa.Column("failure_threshold", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("success_threshold", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_checks_workspace_id", "checks", ["workspace_id"])
    op.create_index("ix_checks_device_id", "checks", ["device_id"])
    op.create_index("ix_checks_type", "checks", ["type"])

    op.create_table(
        "check_states",
        sa.Column("check_id", sa.Integer(), sa.ForeignKey("checks.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("workspace_id", sa.Integer(), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("device_id", sa.Integer(), sa.ForeignKey("devices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("service_name", sa.String(160), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("last_checked", sa.DateTime(timezone=True), nullable=True),
        sa.Column("consecutive_successes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("consecutive_failures", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_check_states_workspace_id", "check_states", ["workspace_id"])
    op.create_index("ix_check_states_device_id", "check_states", ["device_id"])


def downgrade() -> None:
    op.drop_index("ix_check_states_device_id", table_name="check_states")
    op.drop_index("ix_check_states_workspace_id", table_name="check_states")
    op.drop_table("check_states")
    op.drop_index("ix_checks_type", table_name="checks")
    op.drop_index("ix_checks_device_id", table_name="checks")
    op.drop_index("ix_checks_workspace_id", table_name="checks")
    op.drop_table("checks")
    for name in ("check_id", "device_id", "workspace_id"):
        op.drop_index(f"ix_measurements_{name}", table_name="measurements")
        op.drop_column("measurements", name)
