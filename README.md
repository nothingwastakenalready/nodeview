# nodeview

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
- failure/recovery thresholds so one bad sample does not immediately become the apocalypse
- docker because leaving a terminal open forever is stupid

```bash
python -m pip install -e .
cp services.example.yaml services.yaml
nodeview services.yaml
```

or leave it running:

```bash
cp services.example.yaml services.yaml
docker compose up -d
```

by default compose only publishes the api on `127.0.0.1:8080`. there is still no auth, so exposing it to the internet would be a fairly creative decision.

```text
GET  /health
GET  /services
GET  /state
POST /check
```

`/services` runs the configured checks on request. `/state` shows what the scheduler currently believes. `/check` does one ad-hoc http/tcp check without changing config.

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

## where this is going

this stopped being just a cli experiment.

nodeview is heading toward a small self-hosted monitoring thing with history, a web ui, users/workspaces, hexagonal node views, dependency graphs and eventually agents.

not all at once. that would be how this becomes terrible.

next useful problem: persistence and history. current state disappearing on restart is fine for 0.3 and not fine forever.

see `docs/architecture/product-vision.md` and `docs/architecture/roadmap.md` for the longer version.

## dev

```bash
python -m pip install -e '.[test]'
pytest
```

python 3.11+.
