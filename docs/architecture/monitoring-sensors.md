# Monitoring sensors

Raffael keeps the sky interface, but the data model underneath is now closer to
Checkmk, Zabbix and Grafana-style monitoring:

- one star represents one device
- one device can own many sensors
- a sensor is an executable check, for example HTTP, TCP or automatic TCP probe
- the star shows the worst current sensor state for that device
- the selected device panel shows the sensors below that star

## Current sensor data

Every persisted sensor state can expose:

- current status
- current latency
- last check time
- HTTP status, where relevant
- success and failure streaks
- uptime percentage from recent samples
- downtime percentage from recent samples
- average latency from recent samples
- down-event count from recent samples
- technical details such as target, host, port and automatic probe result

The history table stores the same technical details so a restart does not erase
the monitoring evidence.

## Current sensor types

- `http` checks one HTTP or HTTPS URL.
- `tcp` checks one host and port.
- `tcp_auto` checks a device host against known LAN service ports and records the
  first responding port.

These are real reachability and latency checks. They are not placeholders.

## Next sensor types

The next production-grade monitoring work should add connector-backed sensors:

- SNMP for generic network and host metrics
- Proxmox for node, VM, LXC, storage and backup state
- UniFi for clients, APs, switches, ports and controller health
- Docker for container state
- TLS certificate expiry for HTTPS targets
- DNS checks for local resolver health

The design goal is unchanged: the sky stays calm and visual, while the selected
device view carries the serious operational data underneath.
