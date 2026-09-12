"""Client import adapters.

Each source returns the same normalized shape so persistence and UI do not care
whether clients came from UniFi, a generic JSON API, or SNMP.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ClientSourceError(RuntimeError):
    pass


@dataclass(frozen=True)
class ImportedClient:
    name: str
    endpoint: str | None
    mac_address: str | None
    connector: str
    metadata: dict


def clean_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def clean_mac(value: object) -> str | None:
    text = clean_text(value)
    if text is None:
        return None
    normalized = text.lower().replace("-", ":")
    parts = normalized.split(":")
    if len(parts) == 6 and all(len(part) == 2 for part in parts):
        return normalized
    return None


def normalize_client_row(row: dict, *, source: str, connector: str) -> ImportedClient | None:
    mac = clean_mac(row.get("mac_address") or row.get("mac") or row.get("_id"))
    endpoint = clean_text(row.get("endpoint") or row.get("ip") or row.get("address") or row.get("hostname"))
    name = clean_text(row.get("name") or row.get("hostname") or row.get("dns_name") or row.get("label") or row.get("oui"))
    if not name:
        name = endpoint or mac
    if not name:
        return None
    metadata = {"role": "client", "source": source}
    for key, value in row.items():
        if key in {"name", "hostname", "dns_name", "label", "endpoint", "ip", "address", "mac", "mac_address", "_id"}:
            continue
        if value not in (None, ""):
            metadata[f"{source}_{key}"] = value
    return ImportedClient(name=name, endpoint=endpoint, mac_address=mac, connector=connector, metadata=metadata)


def fetch_api_clients() -> list[ImportedClient]:
    url = clean_text(os.environ.get("RAFFAEL_API_CLIENTS_URL"))
    if not url:
        raise ClientSourceError("api client import is not configured")
    headers = {"Accept": "application/json"}
    token = clean_text(os.environ.get("RAFFAEL_API_CLIENTS_TOKEN"))
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers, method="GET")
    try:
        with urlopen(request, timeout=12) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise ClientSourceError(f"api client import failed with HTTP {exc.code}") from exc
    except (URLError, json.JSONDecodeError) as exc:
        raise ClientSourceError("api client import failed") from exc

    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict):
        rows = payload.get("clients") or payload.get("data") or payload.get("items")
    else:
        rows = None
    if not isinstance(rows, list):
        raise ClientSourceError("api client response must be a list or contain clients/data/items")
    return sorted(
        [client for row in rows if isinstance(row, dict) and (client := normalize_client_row(row, source="api", connector="generic"))],
        key=lambda client: (client.name.lower(), client.endpoint or "", client.mac_address or ""),
    )


def fetch_snmp_clients() -> list[ImportedClient]:
    targets = [
        item.strip()
        for item in os.environ.get("RAFFAEL_SNMP_TARGETS", "").split(",")
        if item.strip()
    ]
    if not targets:
        raise ClientSourceError("snmp client import is not configured")
    try:
        from pysnmp.hlapi import (  # type: ignore
            CommunityData,
            ContextData,
            ObjectIdentity,
            ObjectType,
            SnmpEngine,
            UdpTransportTarget,
            getCmd,
        )
    except ImportError as exc:
        raise ClientSourceError("snmp support needs pysnmp installed") from exc

    community = os.environ.get("RAFFAEL_SNMP_COMMUNITY", "public")
    port = int(os.environ.get("RAFFAEL_SNMP_PORT", "161"))
    clients: list[ImportedClient] = []
    for target in targets:
        try:
            result = next(getCmd(
                SnmpEngine(),
                CommunityData(community, mpModel=1),
                UdpTransportTarget((target, port), timeout=2, retries=1),
                ContextData(),
                ObjectType(ObjectIdentity("1.3.6.1.2.1.1.5.0")),
            ))
        except Exception as exc:  # pragma: no cover - depends on optional SNMP stack
            raise ClientSourceError(f"snmp request failed for {target}") from exc
        error_indication, error_status, _, var_binds = result
        if error_indication or error_status:
            raise ClientSourceError(f"snmp request failed for {target}")
        sys_name = clean_text(var_binds[0][1]) if var_binds else None
        clients.append(ImportedClient(
            name=sys_name or target,
            endpoint=target,
            mac_address=None,
            connector="snmp",
            metadata={"role": "client", "source": "snmp", "snmp_sys_name": sys_name or target},
        ))
    return sorted(clients, key=lambda client: client.name.lower())
