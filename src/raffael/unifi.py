"""Small UniFi Network client importer.

Credentials come from environment variables. They are never stored in the
Raffael database.
"""

from __future__ import annotations

import json
import os
import ssl
from http.cookiejar import CookieJar
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import HTTPCookieProcessor, HTTPSHandler, Request, build_opener

from .client_sources import ClientSourceError, ImportedClient, clean_mac, clean_text


class UniFiImportError(ClientSourceError):
    pass


def normalize_unifi_client(row: dict) -> ImportedClient | None:
    mac = clean_mac(row.get("mac") or row.get("_id"))
    endpoint = clean_text(row.get("ip") or row.get("hostname"))
    name = clean_text(row.get("name") or row.get("hostname") or row.get("dns_name") or row.get("oui"))
    if not name:
        name = endpoint or mac
    if not name:
        return None
    metadata = {
        "role": "client",
        "source": "unifi",
    }
    for key in ("hostname", "essid", "network", "oui", "ap_mac", "sw_mac", "last_seen", "is_wired"):
        if key in row and row[key] not in (None, ""):
            metadata[f"unifi_{key}"] = row[key]
    return ImportedClient(name=name, endpoint=endpoint, mac_address=mac, connector="unifi", metadata=metadata)


def fetch_unifi_clients(config: dict | None = None) -> list[ImportedClient]:
    config = config or {}
    base_url = clean_text(config.get("url")) or clean_text(os.environ.get("RAFFAEL_UNIFI_URL"))
    username = clean_text(config.get("username")) or clean_text(os.environ.get("RAFFAEL_UNIFI_USERNAME"))
    password = clean_text(config.get("password")) or clean_text(os.environ.get("RAFFAEL_UNIFI_PASSWORD"))
    api_key = clean_text(config.get("api_key")) or clean_text(os.environ.get("RAFFAEL_UNIFI_API_KEY"))
    site = clean_text(config.get("site")) or clean_text(os.environ.get("RAFFAEL_UNIFI_SITE")) or "default"
    console_id = clean_text(config.get("console_id")) or clean_text(os.environ.get("RAFFAEL_UNIFI_CONSOLE_ID"))
    if not base_url or (not api_key and (not username or not password)):
        raise UniFiImportError("unifi connection is not configured")

    verify_tls = os.environ.get("RAFFAEL_UNIFI_VERIFY_TLS", "0") == "1"
    context = None if verify_tls else ssl._create_unverified_context()
    handlers = [HTTPCookieProcessor(CookieJar())]
    if context is not None:
        handlers.append(HTTPSHandler(context=context))
    opener = build_opener(*handlers)
    try:
        if api_key:
            if urlparse(base_url).hostname == "api.ui.com" or console_id:
                clients = fetch_cloud_clients(opener, base_url, site, api_key, console_id)
            else:
                try:
                    clients = get_json(opener, base_url, f"/proxy/network/api/s/{site}/stat/sta", api_key=api_key)
                except UniFiImportError:
                    clients = fetch_local_integration_clients(opener, base_url, site, api_key)
        else:
            login_response = request_json(
                opener,
                base_url,
                "/api/auth/login",
                {"username": username, "password": password},
            )
            csrf_token = login_response.get("csrfToken") or login_response.get("csrf_token")
            clients = get_json(
                opener,
                base_url,
                f"/proxy/network/api/s/{site}/stat/sta",
                csrf_token=csrf_token,
            )
    except UniFiImportError:
        if api_key:
            raise
        request_json(
            opener,
            base_url,
            "/api/login",
            {"username": username, "password": password},
        )
        clients = get_json(opener, base_url, f"/api/s/{site}/stat/sta")

    rows = clients.get("data")
    if not isinstance(rows, list):
        raise UniFiImportError("unifi clients response is invalid")
    normalized = [client for row in rows if isinstance(row, dict) and (client := normalize_unifi_client(row))]
    return sorted(normalized, key=lambda client: (client.name.lower(), client.endpoint or "", client.mac_address or ""))


def fetch_cloud_clients(opener, base_url: str, site: str, api_key: str, console_id: str | None) -> dict:
    """Fetch clients through UniFi's cloud connector, resolving host/site IDs when omitted."""
    cloud_url = "https://api.ui.com"
    if urlparse(base_url).hostname == "api.ui.com":
        cloud_url = base_url.rstrip("/")
    if not console_id:
        sites = get_json(opener, cloud_url, "/v1/sites", api_key=api_key)
        entries = sites.get("data") if isinstance(sites, dict) else None
        if not isinstance(entries, list) or not entries:
            raise UniFiImportError("unifi cloud returned no sites")
        match = next((row for row in entries if isinstance(row, dict) and (
            row.get("siteId") == site or row.get("id") == site or
            (isinstance(row.get("meta"), dict) and row["meta"].get("name") == site)
        )), entries[0])
        console_id = clean_text(match.get("hostId"))
        site = clean_text(match.get("siteId")) or site
    if not console_id:
        raise UniFiImportError("unifi cloud response has no console id")
    return get_json(
        opener,
        cloud_url,
        f"/v1/connector/consoles/{console_id}/network/integration/v1/sites/{site}/clients",
        api_key=api_key,
    )


def fetch_local_integration_clients(opener, base_url: str, site: str, api_key: str) -> dict:
    """Use the versioned local Network Integration API and resolve site names."""
    sites = get_json(opener, base_url, "/proxy/network/integration/v1/sites", api_key=api_key)
    entries = sites.get("data") if isinstance(sites, dict) else None
    if not isinstance(entries, list) or not entries:
        raise UniFiImportError("unifi local API returned no sites")
    match = next((row for row in entries if isinstance(row, dict) and (
        row.get("id") == site or row.get("internalReference") == site or row.get("name") == site
    )), entries[0])
    site_id = clean_text(match.get("id")) or clean_text(match.get("internalReference"))
    if not site_id:
        raise UniFiImportError("unifi local API returned no site id")
    return get_json(opener, base_url, f"/proxy/network/integration/v1/sites/{site_id}/clients", api_key=api_key)


def request_json(opener, base_url: str, path: str, payload: dict) -> dict:
    request = Request(
        urljoin(base_url.rstrip("/") + "/", path.lstrip("/")),
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    return open_json(opener, request)


def get_json(opener, base_url: str, path: str, csrf_token: str | None = None, api_key: str | None = None) -> dict:
    headers = {"Accept": "application/json"}
    if csrf_token:
        headers["X-CSRF-Token"] = csrf_token
    if api_key:
        headers["X-API-KEY"] = api_key
    request = Request(
        urljoin(base_url.rstrip("/") + "/", path.lstrip("/")),
        headers=headers,
        method="GET",
    )
    return open_json(opener, request)


def open_json(opener, request: Request) -> dict:
    try:
        response = opener.open(request, timeout=12)
    except HTTPError as exc:
        raise UniFiImportError(f"unifi request failed with HTTP {exc.code}") from exc
    except URLError as exc:
        raise UniFiImportError("unifi request failed") from exc
    with response:
        return json.loads(response.read().decode("utf-8"))
