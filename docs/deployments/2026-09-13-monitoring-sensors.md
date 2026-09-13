# monitoring sensors production deployment

date: 2026-09-13

## release

- proxmox vm: `105 (raffael)`
- application directory: `/opt/raffael`
- lan endpoint: `http://192.168.1.147:8080`
- application commit: `57f4f91 fix: refine authentication actions`
- feature commit: `0f0f334 feat: add workspace monitoring sensors`

## data safety and migration

- the application container was stopped before copying sqlite.
- backup: `backups/raffael-before-deploy-20260913-082102.db`
- sqlite integrity before migration: `ok`
- alembic upgrades `20260913_01` and `20260913_02`: passed
- the persistent docker volume was retained.

## verification

- docker image rebuild: passed
- container recreation: passed
- `/health`: `{"status":"ok"}`
- `/ready`: `{"status":"ok","database":"ok","scheduler":"ok"}`
- health and readiness were verified from the vm and from the lan client.
- the live dashboard displays real http/tcp sensor state and latency.
- stored measurements supply uptime, downtime, average latency, down events,
  success/failure streaks and technical target details.
- existing devices were assigned executable default sensors when their endpoint
  supports http, tcp or automatic tcp reachability.
- the sky/constellation layout remains unchanged.
- the obsolete authenticated `sign in` action and the misleading
  constellation-level `3 configured` label are removed.

## security status

the passive owasp zap baseline report in the local `security-reports/2026-09-13`
directory has no high or critical alerts. one csp warning remains because the
constellation currently uses inline positioning. Active testing remains limited
to an isolated test instance and is not run against real lan devices.

this release is approved as a private lan mvp. it is not an approval for direct
public internet exposure.
