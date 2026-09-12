# household connectors

Raffael treats a household as the user's current workspace. Devices are owned
by that workspace and are represented through a connector rather than through
one universal device API.

## connector boundary

The initial catalog contains:

- `unifi` — local UniFi Network API
- `hue` — Philips Hue Bridge API
- `proxmox` — Proxmox REST API
- `windows-agent` — local Windows telemetry agent
- `macos-agent` — local macOS telemetry agent
- `generic` — HTTP/TCP health checks

`GET /integrations/catalog` exposes this catalog to the UI. `GET
/household/devices` lists devices in the current workspace. `POST
/household/devices` creates a pending device record.

## client import sources

Raffael must not depend on one vendor. UniFi is only one adapter behind a
shared source contract:

```text
source -> normalized client -> workspace device
```

All import sources return the same normalized client fields:

- `name`
- `endpoint`
- `mac_address`
- `connector`
- `metadata`

`POST /integrations/{source}/clients/import` imports clients from a configured
source and upserts them by MAC address or endpoint. This keeps repeated imports
safe and avoids duplicate clients.

Current source adapters:

- `unifi` reads clients from a UniFi Network API.
- `api` reads clients from a generic JSON endpoint.
- `snmp` reads a configured target list and imports reachable SNMP devices as
  clients for the first SNMP slice.

Current Docker configuration:

- `RAFFAEL_UNIFI_URL`, for example `https://192.168.1.1`
- `RAFFAEL_UNIFI_USERNAME`
- `RAFFAEL_UNIFI_PASSWORD`
- `RAFFAEL_UNIFI_SITE`, default `default`
- `RAFFAEL_UNIFI_VERIFY_TLS`, default `0` for self-signed local controllers
- `RAFFAEL_API_CLIENTS_URL`
- `RAFFAEL_API_CLIENTS_TOKEN`, optional bearer token
- `RAFFAEL_SNMP_TARGETS`, comma-separated hosts or IP addresses
- `RAFFAEL_SNMP_COMMUNITY`, default `public`
- `RAFFAEL_SNMP_PORT`, default `161`

The current slice stores connector metadata and a credential reference only.
It must never store passwords, API tokens or private keys in `metadata_json` or
in API responses. Credential resolution belongs to a later connector runtime
using an OS keychain, environment-backed secret store or another explicitly
configured local secret provider.

## discovery direction

Discovery is intentionally separate from persistence:

1. a local connector discovers candidates on the LAN;
2. the user reviews and selects candidates;
3. Raffael persists the selected device in the workspace;
4. the connector reports normalized health and telemetry;
5. topology derives relationships from observed dependencies.

The server must not blindly scan or enroll every device. Enrollment requires an
explicit user action and least-privilege credentials. Agents should use an
outbound authenticated connection and must not provide arbitrary remote command
execution.
