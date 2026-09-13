"""Workspace-owned monitor checks and current check states."""

from __future__ import annotations

import ipaddress
import json
import os
import socket
from dataclasses import asdict
from datetime import datetime, timezone
from urllib.parse import urlparse

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from .config import Service
from .engine import ServiceState
from .history import Base, MeasurementRow
from .households import DeviceRow


CHECK_TYPES = {"http", "tcp", "tcp_auto"}
DEFAULT_ALLOWED_NETWORKS = "127.0.0.0/8,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,::1/128,fc00::/7"
DENIED_IPS = {ipaddress.ip_address("169.254.169.254")}


class CheckRow(Base):
    __tablename__ = "checks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    type: Mapped[str] = mapped_column(String(16), index=True)
    url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    host: Mapped[str | None] = mapped_column(String(255), nullable=True)
    port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    interval: Mapped[float] = mapped_column(Float, default=30.0)
    timeout: Mapped[float] = mapped_column(Float, default=2.0)
    failure_threshold: Mapped[int] = mapped_column(Integer, default=2)
    success_threshold: Mapped[int] = mapped_column(Integer, default=1)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class CheckStateRow(Base):
    __tablename__ = "check_states"

    check_id: Mapped[int] = mapped_column(ForeignKey("checks.id", ondelete="CASCADE"), primary_key=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"), index=True)
    service_name: Mapped[str] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(32), default="pending")
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_checked: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    consecutive_successes: Mapped[int] = mapped_column(Integer, default=0)
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)
    details_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class CheckStore:
    def __init__(self, engine):
        self.engine = engine

    def list(self, workspace_id: int) -> list[dict]:
        with Session(self.engine) as session:
            rows = session.scalars(
                select(CheckRow)
                .where(CheckRow.workspace_id == workspace_id)
                .order_by(CheckRow.id)
            ).all()
            return [serialize_check(row) for row in rows]

    def active_services(self) -> list[Service]:
        with Session(self.engine) as session:
            rows = session.scalars(select(CheckRow).where(CheckRow.active.is_(True)).order_by(CheckRow.id)).all()
            return [service_from_check(row) for row in rows]

    def ensure_default_checks(self, workspace_id: int | None = None) -> int:
        created = 0
        with Session(self.engine) as session:
            statement = select(DeviceRow).order_by(DeviceRow.id)
            if workspace_id is not None:
                statement = statement.where(DeviceRow.workspace_id == workspace_id)
            devices = [serialize_device_for_check(row) for row in session.scalars(statement).all()]
        for device in devices:
            if self.create_for_device_target(int(device["workspace_id"]), device) is not None:
                created += 1
        return created

    def get(self, workspace_id: int, check_id: int) -> dict:
        with Session(self.engine) as session:
            row = session.scalar(select(CheckRow).where(CheckRow.workspace_id == workspace_id, CheckRow.id == check_id))
            if row is None:
                raise ValueError("check not found")
            return serialize_check(row)

    def service(self, workspace_id: int, check_id: int) -> Service:
        with Session(self.engine) as session:
            row = session.scalar(select(CheckRow).where(CheckRow.workspace_id == workspace_id, CheckRow.id == check_id))
            if row is None:
                raise ValueError("check not found")
            return service_from_check(row)

    def create(self, workspace_id: int, data: dict) -> dict:
        now = datetime.now(timezone.utc)
        clean = normalize_check(data)
        with Session(self.engine) as session:
            device = session.scalar(select(DeviceRow).where(DeviceRow.workspace_id == workspace_id, DeviceRow.id == clean["device_id"]))
            if device is None:
                raise ValueError("device not found")
            row = CheckRow(workspace_id=workspace_id, created_at=now, updated_at=now, **clean)
            session.add(row)
            session.flush()
            session.add(
                CheckStateRow(
                    check_id=row.id,
                    workspace_id=workspace_id,
                    device_id=row.device_id,
                    service_name=row.name,
                    status="pending",
                    consecutive_successes=0,
                    consecutive_failures=0,
                )
            )
            session.commit()
            session.refresh(row)
            return serialize_check(row)

    def create_for_device_target(self, workspace_id: int, device: dict) -> dict | None:
        payload = check_payload_for_device(device)
        if payload is None:
            return None
        if self.device_has_check(workspace_id, int(device["id"])):
            return None
        try:
            return self.create(workspace_id, payload)
        except ValueError:
            return None

    def device_has_check(self, workspace_id: int, device_id: int) -> bool:
        with Session(self.engine) as session:
            return session.scalar(
                select(CheckRow.id).where(
                    CheckRow.workspace_id == workspace_id,
                    CheckRow.device_id == device_id,
                )
            ) is not None

    def update(self, workspace_id: int, check_id: int, data: dict) -> dict:
        clean = normalize_check(data, partial=True)
        with Session(self.engine) as session:
            row = session.scalar(select(CheckRow).where(CheckRow.workspace_id == workspace_id, CheckRow.id == check_id))
            if row is None:
                raise ValueError("check not found")
            if "device_id" in clean:
                device = session.scalar(select(DeviceRow).where(DeviceRow.workspace_id == workspace_id, DeviceRow.id == clean["device_id"]))
                if device is None:
                    raise ValueError("device not found")
            for key, value in clean.items():
                setattr(row, key, value)
            row.updated_at = datetime.now(timezone.utc)
            state = session.get(CheckStateRow, check_id)
            if state is not None:
                state.device_id = row.device_id
                state.service_name = row.name
                state.workspace_id = row.workspace_id
            session.commit()
            session.refresh(row)
            return serialize_check(row)

    def delete(self, workspace_id: int, check_id: int) -> None:
        with Session(self.engine) as session:
            row = session.scalar(select(CheckRow).where(CheckRow.workspace_id == workspace_id, CheckRow.id == check_id))
            if row is None:
                raise ValueError("check not found")
            session.delete(row)
            session.commit()

    def states(self, workspace_id: int) -> list[dict]:
        with Session(self.engine) as session:
            rows = session.scalars(
                select(CheckStateRow)
                .where(CheckStateRow.workspace_id == workspace_id)
                .order_by(CheckStateRow.check_id)
            ).all()
            availability = availability_for_checks(session, workspace_id, [row.check_id for row in rows])
            return [serialize_state(row, availability.get(row.check_id)) for row in rows]

    def record(self, state: ServiceState) -> None:
        if state.check_id is None or state.workspace_id is None or state.device_id is None:
            return
        with Session(self.engine) as session:
            row = session.get(CheckStateRow, state.check_id)
            if row is None:
                row = CheckStateRow(
                    check_id=state.check_id,
                    workspace_id=state.workspace_id,
                    device_id=state.device_id,
                    service_name=state.name,
                )
                session.add(row)
            row.workspace_id = state.workspace_id
            row.device_id = state.device_id
            row.service_name = state.name
            row.status = state.status
            row.latency_ms = state.latency_ms
            row.http_status = state.http_status
            row.error = state.error
            row.last_checked = state.last_checked
            row.consecutive_successes = state.consecutive_successes
            row.consecutive_failures = state.consecutive_failures
            row.details_json = json.dumps(state.details) if state.details else None
            device = session.get(DeviceRow, state.device_id)
            if device is not None:
                device.status = state.status
                device.updated_at = datetime.now(timezone.utc)
            session.commit()


class CompositeRecorder:
    def __init__(self, *recorders):
        self._recorders = [recorder for recorder in recorders if recorder is not None]

    def record(self, state: ServiceState) -> None:
        for recorder in self._recorders:
            recorder.record(state)


def normalize_check(data: dict, partial: bool = False) -> dict:
    allowed = {
        "device_id",
        "name",
        "type",
        "url",
        "host",
        "port",
        "interval",
        "timeout",
        "failure_threshold",
        "success_threshold",
        "active",
    }
    clean = {key: value for key, value in data.items() if key in allowed}
    required = {"device_id", "name", "type"} if not partial else set()
    missing = [key for key in required if clean.get(key) in (None, "")]
    if missing:
        raise ValueError(f"{', '.join(missing)} required")

    if "name" in clean:
        clean["name"] = str(clean["name"]).strip()
        if not clean["name"] or len(clean["name"]) > 160:
            raise ValueError("check name required")
    if "type" in clean:
        clean["type"] = str(clean["type"]).lower().strip()
        if clean["type"] not in CHECK_TYPES:
            raise ValueError("check type must be http, tcp or tcp_auto")
    if "url" in clean and clean["url"]:
        clean["url"] = str(clean["url"]).strip()
        parsed = urlparse(clean["url"])
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("http checks need an http or https url")
        validate_target_host(parsed.hostname)
    if "host" in clean and clean["host"]:
        clean["host"] = str(clean["host"]).strip()
        validate_target_host(clean["host"])
    if "port" in clean and clean["port"] is not None:
        clean["port"] = int(clean["port"])
        if clean["port"] < 1 or clean["port"] > 65535:
            raise ValueError("tcp port must be between 1 and 65535")
    for key, default, minimum, maximum in (
        ("interval", 30.0, 1.0, 86400.0),
        ("timeout", 2.0, 0.1, 60.0),
        ("failure_threshold", 2, 1, 100),
        ("success_threshold", 1, 1, 100),
    ):
        if key in clean:
            value = float(clean[key]) if isinstance(default, float) else int(clean[key])
            if value < minimum or value > maximum:
                raise ValueError(f"{key} must be between {minimum} and {maximum}")
            clean[key] = value
        elif not partial:
            clean[key] = default
    if "active" in clean:
        clean["active"] = bool(clean["active"])
    elif not partial:
        clean["active"] = True

    kind = clean.get("type")
    if kind == "http" and not clean.get("url"):
        raise ValueError("http checks need a url")
    if kind == "tcp" and (not clean.get("host") or clean.get("port") is None):
        raise ValueError("tcp checks need a host and port")
    if kind == "tcp_auto" and not clean.get("host"):
        raise ValueError("tcp auto checks need a host")
    if kind == "http":
        clean["host"] = None
        clean["port"] = None
    if kind == "tcp":
        clean["url"] = None
    if kind == "tcp_auto":
        clean["url"] = None
        clean["port"] = None
    return clean


def check_payload_for_device(device: dict) -> dict | None:
    endpoint = str(device.get("endpoint") or "").strip()
    if not endpoint:
        return None
    name = str(device.get("name") or endpoint)
    device_id = int(device["id"])
    parsed = urlparse(endpoint)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return {
            "device_id": device_id,
            "name": name,
            "type": "http",
            "url": endpoint,
            "interval": 30.0,
        }

    host, port = split_host_port(endpoint)
    if host and port is not None:
        return {
            "device_id": device_id,
            "name": name,
            "type": "tcp",
            "host": host,
            "port": port,
            "interval": 30.0,
        }

    open_ports = device.get("metadata", {}).get("open_ports", [])
    if isinstance(open_ports, list) and open_ports:
        port = int(open_ports[0])
        return {
            "device_id": device_id,
            "name": name,
            "type": "tcp",
            "host": endpoint,
            "port": port,
            "interval": 30.0,
        }
    return {
        "device_id": device_id,
        "name": name,
        "type": "tcp_auto",
        "host": endpoint,
        "interval": 30.0,
        "timeout": 0.5,
    }


def split_host_port(endpoint: str) -> tuple[str | None, int | None]:
    if endpoint.count(":") != 1:
        return None, None
    host, port_value = endpoint.rsplit(":", 1)
    if not host or not port_value.isdigit():
        return None, None
    port = int(port_value)
    if port < 1 or port > 65535:
        return None, None
    return host, port


def validate_target_host(host: str | None) -> None:
    if not host:
        raise ValueError("check target host required")
    try:
        candidates = [ipaddress.ip_address(host.strip("[]"))]
    except ValueError:
        try:
            candidates = [
                ipaddress.ip_address(item[4][0])
                for item in socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
            ]
        except socket.gaierror as exc:
            raise ValueError("check target could not be resolved") from exc

    allowed_networks = [
        ipaddress.ip_network(item.strip(), strict=False)
        for item in os.environ.get("RAFFAEL_ALLOWED_CHECK_NETWORKS", DEFAULT_ALLOWED_NETWORKS).split(",")
        if item.strip()
    ]
    for address in set(candidates):
        if address in DENIED_IPS or address.is_link_local or address.is_multicast or address.is_unspecified:
            raise ValueError("check target is not allowed")
        if not any(address in network for network in allowed_networks):
            raise ValueError("check target is outside allowed networks")


def service_from_check(row: CheckRow) -> Service:
    return Service(
        name=row.name,
        url=row.url,
        host=row.host,
        port=row.port,
        type=row.type,
        interval=row.interval,
        timeout=row.timeout,
        failure_threshold=row.failure_threshold,
        success_threshold=row.success_threshold,
        check_id=row.id,
        workspace_id=row.workspace_id,
        device_id=row.device_id,
    )


def serialize_device_for_check(row: DeviceRow) -> dict:
    from .households import serialize_device

    return serialize_device(row)


def serialize_check(row: CheckRow) -> dict:
    return {
        "id": row.id,
        "workspace_id": row.workspace_id,
        "device_id": row.device_id,
        "name": row.name,
        "type": row.type,
        "url": row.url,
        "host": row.host,
        "port": row.port,
        "interval": row.interval,
        "timeout": row.timeout,
        "failure_threshold": row.failure_threshold,
        "success_threshold": row.success_threshold,
        "active": row.active,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }


def availability_for_checks(session: Session, workspace_id: int, check_ids: list[int], limit: int = 100) -> dict[int, dict]:
    if not check_ids:
        return {}
    result: dict[int, dict] = {}
    for check_id in check_ids:
        rows = session.scalars(
            select(MeasurementRow)
            .where(
                MeasurementRow.workspace_id == workspace_id,
                MeasurementRow.check_id == check_id,
            )
            .order_by(MeasurementRow.checked_at.desc(), MeasurementRow.id.desc())
            .limit(limit)
        ).all()
        samples = len(rows)
        if samples == 0:
            result[check_id] = {
                "availability_samples": 0,
                "uptime_pct": None,
                "downtime_pct": None,
                "avg_latency_ms": None,
                "down_events": 0,
            }
            continue
        up_samples = sum(1 for row in rows if row.status == "up")
        down_samples = sum(1 for row in rows if row.status in {"critical", "unknown"})
        latencies = [row.latency_ms for row in rows if row.latency_ms is not None]
        result[check_id] = {
            "availability_samples": samples,
            "uptime_pct": round((up_samples / samples) * 100, 1),
            "downtime_pct": round((down_samples / samples) * 100, 1),
            "avg_latency_ms": round(sum(latencies) / len(latencies)) if latencies else None,
            "down_events": down_samples,
        }
    return result


def serialize_state(row: CheckStateRow, availability: dict | None = None) -> dict:
    payload = asdict(
        ServiceState(
            name=row.service_name,
            status=row.status,
            latency_ms=row.latency_ms,
            http_status=row.http_status,
            error=row.error,
            last_checked=row.last_checked.replace(tzinfo=row.last_checked.tzinfo or timezone.utc) if row.last_checked else None,
            consecutive_successes=row.consecutive_successes,
            consecutive_failures=row.consecutive_failures,
            check_id=row.check_id,
            workspace_id=row.workspace_id,
            device_id=row.device_id,
            details=json.loads(row.details_json) if row.details_json else None,
        )
    )
    payload.update(
        availability
        or {
            "availability_samples": 0,
            "uptime_pct": None,
            "downtime_pct": None,
            "avg_latency_ms": None,
            "down_events": 0,
        }
    )
    return payload
