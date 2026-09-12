"""Workspace-owned household devices and connector metadata.

Secrets are deliberately not stored here. Connector implementations receive a
credential reference and resolve it through an OS/environment secret store.
"""

import json
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from .history import Base


@dataclass(frozen=True)
class ConnectorSpec:
    key: str
    label: str
    transport: str
    discovery: str
    note: str


CONNECTORS = (
    ConnectorSpec("unifi", "UniFi", "local api", "network api", "network devices and clients"),
    ConnectorSpec("hue", "Philips Hue", "local bridge api", "mdns / bridge", "bridge and lights"),
    ConnectorSpec("proxmox", "Proxmox", "rest api", "manual endpoint", "nodes and virtual machines"),
    ConnectorSpec("windows-agent", "Windows", "local agent", "lan agent", "host telemetry"),
    ConnectorSpec("macos-agent", "macOS", "local agent", "lan agent", "host telemetry"),
    ConnectorSpec("generic", "Generic service", "http / tcp", "manual endpoint", "custom health check"),
)
CONNECTOR_KEYS = {item.key for item in CONNECTORS}


class DeviceRow(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    connector: Mapped[str] = mapped_column(String(32), index=True)
    name: Mapped[str] = mapped_column(String(160))
    endpoint: Mapped[str | None] = mapped_column(String(512), nullable=True)
    credential_ref: Mapped[str | None] = mapped_column(String(256), nullable=True)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    status: Mapped[str] = mapped_column(String(16), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


def connector_catalog() -> list[dict[str, str]]:
    return [item.__dict__ for item in CONNECTORS]


class DeviceStore:
    def __init__(self, engine):
        self.engine = engine

    def list(self, workspace_id: int) -> list[dict]:
        with Session(self.engine) as session:
            rows = session.scalars(
                select(DeviceRow).where(DeviceRow.workspace_id == workspace_id).order_by(DeviceRow.id)
            ).all()
            return [serialize_device(row) for row in rows]

    def create(
        self,
        workspace_id: int,
        connector: str,
        name: str,
        endpoint: str | None = None,
        credential_ref: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        if connector not in CONNECTOR_KEYS:
            raise ValueError("unsupported connector")
        clean_name = name.strip()
        if not clean_name or len(clean_name) > 160:
            raise ValueError("device name required")
        now = datetime.now(timezone.utc)
        row = DeviceRow(
            workspace_id=workspace_id,
            connector=connector,
            name=clean_name,
            endpoint=endpoint.strip() if endpoint else None,
            credential_ref=credential_ref.strip() if credential_ref else None,
            metadata_json=json.dumps(metadata or {}, separators=(",", ":")),
            status="pending",
            created_at=now,
            updated_at=now,
        )
        with Session(self.engine) as session:
            session.add(row)
            session.commit()
            session.refresh(row)
            return serialize_device(row)


def serialize_device(row: DeviceRow) -> dict:
    try:
        metadata = json.loads(row.metadata_json or "{}")
    except json.JSONDecodeError:
        metadata = {}
    return {
        "id": row.id,
        "workspace_id": row.workspace_id,
        "connector": row.connector,
        "name": row.name,
        "endpoint": row.endpoint,
        "credential_ref": row.credential_ref,
        "metadata": metadata,
        "status": row.status,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }
