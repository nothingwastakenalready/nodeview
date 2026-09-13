# raffael

i have too many random things running at home and got tired of checking them one by one.

so this checks them.

there are obviously a hundred tools that do this already. i didn't want any of them.

## right now

- local account login
- database-backed devices and sensors
- http + tcp checks
- response time
- latency, uptime and downtime from stored history
- http api
- always-on scheduler
- current state with `pending / up / warning / critical / unknown`
- durable sqlite measurement history
- bounded per-service history api with utc time ranges
- failure/recovery thresholds so one bad sample does not immediately become the apocalypse
- browser ui with a starfield/constellation overview
- docker because leaving a terminal open forever is stupid
- local Mailpit inbox for safe email development

## if you found this

If you want to make it run without knowing the project already, start here:

```text
docs/getting-started.md
```

That guide explains Docker, `.env`, the first account, Mailpit and the first
sensor without assuming you know this repo already.

Configuration reference:

```text
docs/configuration.md
```

## run it locally

You only need Git and Docker Desktop (or Docker Engine + Compose).

```bash
git clone https://github.com/nothingwastakenalready/raffael.git
cd raffael
cp .env.example .env
cp services.example.yaml services.yaml
docker compose up -d --build
```

Then open:

```text
http://127.0.0.1:8080
```

For local email development, open the Mailpit inbox at:

```text
http://127.0.0.1:8025
```

Mailpit captures messages locally and does not deliver them to real recipients.
See `docs/architecture/email-delivery.md` for Proton SMTP configuration and
the planned confirmation/newsletter flows.

The same process serves the API, scheduler and built UI. Compose binds only to
localhost by default. Keep it that way unless you deliberately want LAN access.
For LAN access, edit `.env` and set the bind addresses and public URL to the
host's LAN IP:

```env
RAFFAEL_BIND_ADDRESS=192.168.1.50
RAFFAEL_MAILPIT_BIND_ADDRESS=192.168.1.50
RAFFAEL_PUBLIC_URL=http://192.168.1.50:8080
```

Do not expose Raffael directly to the public internet.

Create the first account in the browser. If you need password reset or account
email, open Mailpit and use the newest message.

Add real sensors from the dashboard, or change `services.yaml` before the first
database import, then restart:

```bash
docker compose restart
```

API is still there:

```text
GET  /health
GET  /ready
GET  /state
GET  /checks
POST /checks
PATCH /checks/{check_id}
DELETE /checks/{check_id}
GET  /checks/{check_id}/history
POST /checks/{check_id}/run
```

`/ready` checks database and scheduler readiness. `/state` shows the current
workspace-filtered monitoring state. `/checks` manages stored sensors. The old
raw `/check` endpoint is intentionally gone for normal use.

config is still deliberately boring:

```yaml
services:
  - name: example
    url: https://example.com
    interval: 30
    failure_threshold: 2
    success_threshold: 1

  - name: ssh
    type: tcp
    host: 192.0.2.10
    port: 22
    timeout: 2
```

monitoring fields are optional. defaults are 30s interval, two failures before critical and one success to recover.

`services.yaml` is ignored on purpose. i'm eventually pointing this at things that don't need to be on github.

## ui dev

The first UI is deliberately small and easy to change. Run the API on `127.0.0.1:8080`, then:

```bash
cd web
npm install
npm run dev
```

Vite proxies the Raffael API during development. The production Docker image builds the frontend and serves it from FastAPI, so there is no second service to operate.

The current screen uses services as overview tiles because the real node/workspace model does not exist yet. That is temporary and documented in `docs/architecture/ui.md`.

## where this is going

this stopped being just a cli experiment.

raffael is heading toward a small self-hosted monitoring thing with history, users/workspaces, a proper node model, dependency graphs and eventually agents.

not all at once. that would be how this becomes terrible.

v0.4 has started with durable measurement history. retention, uptime aggregation and state-change events are the next pieces of that backend slice.

see `docs/architecture/product-vision.md`, `docs/architecture/roadmap.md` and `docs/architecture/ui.md` for the longer version.

The reproducible Proxmox/Mini-PC hierarchy test is documented in
`docs/architecture/proxmox-minipc-test.md`.

The monitoring data model is documented in
`docs/architecture/monitoring-sensors.md`: one star remains one device, while
multiple executable sensors can run underneath it.

## dev

```bash
python -m pip install -e '.[test]'
pytest

cd web
npm test
npm run build
```

python 3.11+.

Before deploying, run `scripts/pre-deploy-check.sh` and follow
`docs/deployment.md`.
