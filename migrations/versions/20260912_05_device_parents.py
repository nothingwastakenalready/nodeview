"""add parent relationships to household devices"""

from alembic import op
import sqlalchemy as sa

revision = "20260912_05"
down_revision = "20260912_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # A failed SQLite batch migration can leave Alembic's temporary table
    # behind. Remove it before retrying so the migration is self-healing.
    op.execute("DROP TABLE IF EXISTS _alembic_tmp_devices")
    # SQLite cannot reliably recreate a table with a self-referencing FK
    # while a previous failed batch is present. A nullable column plus index
    # provides the same application behavior without the fragile rebuild.
    op.add_column("devices", sa.Column("parent_id", sa.Integer(), nullable=True))
    op.create_index("ix_devices_parent_id", "devices", ["parent_id"])


def downgrade() -> None:
    op.drop_index("ix_devices_parent_id", table_name="devices")
    op.drop_column("devices", "parent_id")
