# household connectors

raffael treats a household as the user's current workspace. devices are owned
by that workspace and are represented through a connector rather than through
one universal device api.

## connector boundary

the initial catalog contains:

- `unifi` - local unifi network api
- `hue` - philips hue bridge api
- `proxmox` - proxmox rest api
- `windows-agent` - local windows telemetry agent
- `macos-agent` - local macos telemetry agent
- `generic` - http/tcp health checks

`GET /integrations/catalog` exposes this catalog to the UI. `GET
/household/devices` lists devices in the current workspace. `POST
/household/devices` creates a pending device record.

## client import sources

raffael must not depend on one vendor. unifi is only one adapter behind a
shared source contract:

```text
source -> normalized client -> workspace device
```

all import sources return the same normalized client fields:

- `name`
- `endpoint`
- `mac_address`
- `connector`
- `metadata`

`POST /integrations/{source}/clients/import` imports clients from a configured
source and upserts them by mac address or endpoint. this keeps repeated imports
safe and avoids duplicate clients.

current source adapters:

- `unifi` reads clients from a unifi network api.
- `api` reads clients from a generic JSON endpoint.
- `snmp` reads a configured target list and imports reachable snmp devices as
  clients for the first snmp slice.

current docker configuration:

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

the current slice stores connector metadata and a credential reference only.
it must never store passwords, api tokens or private keys in `metadata_json` or
in api responses. credential resolution belongs to a later connector runtime
using an os keychain, environment-backed secret store or another explicitly
configured local secret provider.

## discovery direction

discovery is intentionally separate from persistence:

1. a local connector discovers candidates on the lan;
2. the user reviews and selects candidates;
3. raffael persists the selected device in the workspace;
4. the connector reports normalized health and telemetry;
5. topology derives relationships from observed dependencies.

the server must not blindly scan or enroll every device. enrollment requires an
explicit user action and least-privilege credentials. Agents should use an
outbound authenticated connection and must not provide arbitrary remote command
execution.
