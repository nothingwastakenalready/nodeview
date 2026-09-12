from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text


ROOT = Path(__file__).resolve().parents[1]


def alembic_config(database_path: Path) -> Config:
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path}")
    return config


def current_revision(database_path: Path) -> str:
    engine = create_engine(f"sqlite:///{database_path}")
    try:
        with engine.connect() as connection:
            return connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    finally:
        engine.dispose()


def device_schema(database_path: Path) -> tuple[set[str], set[str], set[str]]:
    engine = create_engine(f"sqlite:///{database_path}")
    try:
        inspector = inspect(engine)
        columns = {column["name"] for column in inspector.get_columns("devices")}
        indexes = {index["name"] for index in inspector.get_indexes("devices")}
        tables = set(inspector.get_table_names())
        return columns, indexes, tables
    finally:
        engine.dispose()


def test_alembic_upgrades_fresh_sqlite_database_to_head(tmp_path):
    database_path = tmp_path / "fresh.db"

    command.upgrade(alembic_config(database_path), "head")

    columns, indexes, tables = device_schema(database_path)
    assert current_revision(database_path) == "20260912_05"
    assert "parent_id" in columns
    assert "ix_devices_parent_id" in indexes
    assert "_alembic_tmp_devices" not in tables


def test_parent_migration_recovers_database_already_changed_but_not_stamped(tmp_path):
    database_path = tmp_path / "partially-migrated.db"
    config = alembic_config(database_path)
    command.upgrade(config, "20260912_04")

    engine = create_engine(f"sqlite:///{database_path}")
    try:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE devices ADD COLUMN parent_id INTEGER"))
            connection.execute(text("CREATE INDEX ix_devices_parent_id ON devices (parent_id)"))
            connection.execute(text("CREATE TABLE _alembic_tmp_devices (id INTEGER)"))
    finally:
        engine.dispose()

    command.upgrade(config, "head")

    columns, indexes, tables = device_schema(database_path)
    assert current_revision(database_path) == "20260912_05"
    assert "parent_id" in columns
    assert "ix_devices_parent_id" in indexes
    assert "_alembic_tmp_devices" not in tables
