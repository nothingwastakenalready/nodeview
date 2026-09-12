"""add parent relationships to household devices"""

from alembic import op
import sqlalchemy as sa

revision = "20260912_05"
down_revision = "20260912_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("devices", recreate="always") as batch:
        batch.add_column(sa.Column("parent_id", sa.Integer(), nullable=True))
        batch.create_index("ix_devices_parent_id", ["parent_id"])
        batch.create_foreign_key("fk_devices_parent_id", "devices", ["parent_id"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    with op.batch_alter_table("devices", recreate="always") as batch:
        batch.drop_constraint("fk_devices_parent_id", type_="foreignkey")
        batch.drop_index("ix_devices_parent_id")
        batch.drop_column("parent_id")
