"""Workspace-owned household devices and connector metadata.

Secrets are deliberately not stored here. Connector implementations receive a
credential reference and resolve it through an OS/environment secret store.
"""

from __future__ import annotations

import json
import re
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
    ConnectorSpec("snmp", "SNMP", "snmp v2c / v3", "lan probe", "network, printer, NAS and UPS telemetry"),
    ConnectorSpec("unifi", "UniFi", "local api", "network api", "network devices and clients"),
    ConnectorSpec("hue", "Philips Hue", "local bridge api", "mdns / bridge", "bridge and lights"),
    ConnectorSpec("proxmox", "Proxmox", "rest api", "manual endpoint", "nodes and virtual machines"),
    ConnectorSpec("windows-agent", "Windows", "local agent", "lan agent", "host telemetry"),
    ConnectorSpec("macos-agent", "macOS", "local agent", "lan agent", "host telemetry"),
    ConnectorSpec("ssh", "SSH Linux", "ssh", "manual endpoint", "host telemetry and services"),
    ConnectorSpec("docker", "Docker", "docker api", "manual endpoint", "containers and compose stacks"),
    ConnectorSpec("icmp", "Ping", "icmp", "network scan", "latency, reachability and downtime"),
    ConnectorSpec("generic", "Generic service", "http / tcp", "manual endpoint", "custom health check"),
)
CONNECTOR_KEYS = {item.key for item in CONNECTORS}
DEVICE_ROLES = {"infrastructure", "service", "client", "iot"}
MAC_ADDRESS_RE = re.compile(r"^[0-9a-f]{2}(?::[0-9a-f]{2}){5}$")


class DeviceRow(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("devices.id", ondelete="SET NULL"), nullable=True, index=True)
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

    def list_clients(self, workspace_id: int) -> list[dict]:
        return [
            item
            for item in self.list(workspace_id)
            if item["metadata"].get("role") == "client"
        ]

    def create(
        self,
        workspace_id: int,
        connector: str,
        name: str,
        endpoint: str | None = None,
        credential_ref: str | None = None,
        metadata: dict | None = None,
        parent_id: int | None = None,
    ) -> dict:
        if connector not in CONNECTOR_KEYS:
            raise ValueError("unsupported connector")
        clean_name = name.strip()
        if not clean_name or len(clean_name) > 160:
            raise ValueError("device name required")
        clean_metadata = normalize_metadata(metadata)
        now = datetime.now(timezone.utc)
        row = DeviceRow(
            workspace_id=workspace_id,
            parent_id=parent_id,
            connector=connector,
            name=clean_name,
            endpoint=endpoint.strip() if endpoint else None,
            credential_ref=credential_ref.strip() if credential_ref else None,
            metadata_json=json.dumps(clean_metadata, separators=(",", ":")),
            status="pending",
            created_at=now,
            updated_at=now,
        )
        with Session(self.engine) as session:
            if parent_id is not None:
                parent = session.scalar(select(DeviceRow).where(DeviceRow.id == parent_id, DeviceRow.workspace_id == workspace_id))
                if parent is None:
                    raise ValueError("parent device not found")
            session.add(row)
            session.commit()
            session.refresh(row)
            return serialize_device(row)

    def create_client(
        self,
        workspace_id: int,
        name: str,
        endpoint: str | None = None,
        mac_address: str | None = None,
        connector: str = "icmp",
        parent_id: int | None = None,
        metadata: dict | None = None,
    ) -> dict:
        clean_metadata = normalize_metadata(metadata)
        clean_metadata["role"] = "client"
        if mac_address:
            clean_mac = mac_address.strip().lower().replace("-", ":")
            if not MAC_ADDRESS_RE.fullmatch(clean_mac):
                raise ValueError("client mac address is invalid")
            clean_metadata["mac_address"] = clean_mac
        return self.create(
            workspace_id,
            connector,
            name,
            endpoint=endpoint,
            metadata=clean_metadata,
            parent_id=parent_id,
        )


def serialize_device(row: DeviceRow) -> dict:
    try:
        metadata = json.loads(row.metadata_json or "{}")
    except json.JSONDecodeError:
        metadata = {}
    return {
        "id": row.id,
        "workspace_id": row.workspace_id,
        "parent_id": row.parent_id,
        "connector": row.connector,
        "name": row.name,
        "endpoint": row.endpoint,
        "credential_ref": row.credential_ref,
        "metadata": metadata,
        "status": row.status,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }


def normalize_metadata(metadata: dict | None) -> dict:
    clean_metadata = dict(metadata or {})
    role = clean_metadata.get("role")
    if role is not None:
        clean_role = str(role).strip().lower()
        if clean_role not in DEVICE_ROLES:
            raise ValueError("unsupported device role")
        clean_metadata["role"] = clean_role
    return clean_metadata
