"""add parent relationships to household devices"""

from alembic import op
import sqlalchemy as sa

revision = "20260912_05"
down_revision = "20260912_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("devices", sa.Column("parent_id", sa.Integer(), nullable=True))
    op.create_index("ix_devices_parent_id", "devices", ["parent_id"])
    op.create_foreign_key("fk_devices_parent_id", "devices", "devices", ["parent_id"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    op.drop_constraint("fk_devices_parent_id", "devices", type_="foreignkey")
    op.drop_index("ix_devices_parent_id", table_name="devices")
    op.drop_column("devices", "parent_id")
