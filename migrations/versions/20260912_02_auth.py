"""add local accounts and sessions

Revision ID: 20260912_02
Revises: 20260912_01
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260912_02"
down_revision: str | None = "20260912_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table("users", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("email", sa.String(320), nullable=False), sa.Column("password_hash", sa.String(512), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table("workspaces", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(120), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("memberships", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("workspace_id", sa.Integer(), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False), sa.Column("role", sa.String(16), nullable=False))
    op.create_index("ix_memberships_user_id", "memberships", ["user_id"])
    op.create_index("ix_memberships_workspace_id", "memberships", ["workspace_id"])
    op.create_index("uq_memberships_user_workspace", "memberships", ["user_id", "workspace_id"], unique=True)
    op.create_table("sessions", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("token_digest", sa.String(64), nullable=False), sa.Column("csrf_digest", sa.String(64), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_sessions_token_digest", "sessions", ["token_digest"], unique=True)
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])
    op.create_index("ix_sessions_expires_at", "sessions", ["expires_at"])


def downgrade() -> None:
    op.drop_table("sessions")
    op.drop_index("uq_memberships_user_workspace", table_name="memberships")
    op.drop_index("ix_memberships_workspace_id", table_name="memberships")
    op.drop_index("ix_memberships_user_id", table_name="memberships")
    op.drop_table("memberships")
    op.drop_table("workspaces")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
