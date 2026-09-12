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
