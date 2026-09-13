# Monitoring sensors production deployment

Date: 2026-09-13

## Release

- Proxmox VM: `105 (raffael)`
- Application directory: `/opt/raffael`
- LAN endpoint: `http://192.168.1.147:8080`
- Application commit: `57f4f91 fix: refine authentication actions`
- Feature commit: `0f0f334 feat: add workspace monitoring sensors`

## Data safety and migration

- The application container was stopped before copying SQLite.
- Backup: `backups/raffael-before-deploy-20260913-082102.db`
- SQLite integrity before migration: `ok`
- Alembic upgrades `20260913_01` and `20260913_02`: passed
- The persistent Docker volume was retained.

## Verification

- Docker image rebuild: passed
- Container recreation: passed
- `/health`: `{"status":"ok"}`
- `/ready`: `{"status":"ok","database":"ok","scheduler":"ok"}`
- Health and readiness were verified from the VM and from the LAN client.
- The live dashboard displays real HTTP/TCP sensor state and latency.
- Stored measurements supply uptime, downtime, average latency, down events,
  success/failure streaks and technical target details.
- Existing devices were assigned executable default sensors when their endpoint
  supports HTTP, TCP or automatic TCP reachability.
- The sky/constellation layout remains unchanged.
- The obsolete authenticated `sign in` action and the misleading
  constellation-level `3 configured` label are removed.

## Security status

The passive OWASP ZAP baseline report in the local `security-reports/2026-09-13`
directory has no High or Critical alerts. One CSP warning remains because the
constellation currently uses inline positioning. Active testing remains limited
to an isolated test instance and is not run against real LAN devices.

This release is approved as a private LAN MVP. It is not an approval for direct
public Internet exposure.
