# raffael

i have too many random things running at home and got tired of checking them one by one.

so this checks them.

there are obviously a hundred tools that do this already. i didn't want any of them.

## right now

- yaml in
- http + tcp checks
- response time
- cli out
- http api
- always-on scheduler
- current state with `pending / up / warning / critical / unknown`
- durable sqlite measurement history
- bounded per-service history api with utc time ranges
- failure/recovery thresholds so one bad sample does not immediately become the apocalypse
- first browser ui with a compact hexagon overview and current latency
- docker because leaving a terminal open forever is stupid
- local Mailpit inbox for safe email development

## run it locally

You only need Git and Docker Desktop (or Docker Engine + Compose).

```bash
git clone https://github.com/nothingwastakenalready/raffael.git
cd raffael
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

The same process serves the API, scheduler and built UI. Compose still binds only to localhost by default. There is no auth yet, so changing that to a public bind would be a fairly creative decision.

Change `services.yaml` to point at things you actually run, then restart:

```bash
docker compose restart
```

API is still there:

```text
GET  /health
GET  /services
GET  /state
GET  /history/{service_name}
POST /check
```

`/services` runs the configured checks on request. `/state` shows what the scheduler currently believes. `/history/{service_name}` returns stored scheduled measurements and accepts optional `from`, `to` and `limit` query parameters. `/check` does one ad-hoc http/tcp check without changing config.

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

## dev

```bash
python -m pip install -e '.[test]'
pytest

cd web
npm test
npm run build
```

python 3.11+.
