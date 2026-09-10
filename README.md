# nodeview

i have too many random things running at home and got tired of checking them one by one.

so this checks them.

there are obviously a hundred tools that do this already. i didn't want any of them.

## right now

- yaml in
- http + tcp checks
- up / down
- response time
- cli out
- tiny http api
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

by default compose only publishes the api on `127.0.0.1:8080`. there is no auth in v0.2, so exposing it to the internet would be a fairly creative decision.

```text
GET  /health
GET  /services
POST /check
```

`/services` runs the configured checks and returns json. `/check` does one ad-hoc http/tcp check without changing config.

config is still deliberately boring:

```yaml
services:
  - name: example
    url: https://example.com

  - name: ssh
    type: tcp
    host: 192.0.2.10
    port: 22
    timeout: 2
```

`services.yaml` is ignored on purpose. i'm eventually pointing this at things that don't need to be on github.

## where this is going

this stopped being just a cli experiment.

nodeview is heading toward a small self-hosted monitoring thing with history, a web ui, users/workspaces, hexagonal node views, dependency graphs and eventually agents.

not all at once. that would be how this becomes terrible.

see `docs/architecture/product-vision.md` and `docs/architecture/roadmap.md` for the longer version.

## dev

```bash
python -m pip install -e '.[test]'
pytest
```

python 3.11+.
