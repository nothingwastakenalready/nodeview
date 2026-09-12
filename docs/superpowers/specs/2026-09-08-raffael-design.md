# raffael design

## why

i have too many random things running at home and got tired of checking them one by one.

there are obviously a hundred tools that already do this. i didn't want any of them.

raffael starts small: give it a list of services, it checks them and tells you what answered.

## v0.1

keep it boring.

- read service definitions from yaml
- check http endpoints
- report up/down
- include response time
- expose the result through a cli
- tests for healthy, failing and timeout-ish cases
- github actions runs the tests

## not now

no dashboard, auth, database, kubernetes, grafana clone, ai, cloud anything or twelve layers of abstraction.

those can become problems later if they actually become problems.

## shape

```text
services.yaml
    |
    v
config loader
    |
    v
http checker
    |
    v
status result
    |
    v
cli
```

## config

public examples never contain real internal addresses or secrets.

```yaml
services:
  - name: example
    url: https://example.com
    timeout: 2.0
```

## result

internally one check result has:

- name
- url
- status: up or down
- latency_ms when a response happened
- http_status when a response happened
- error when it did not

cli output should stay readable instead of pretending to be a monitoring platform.

## stack

python 3.11+

small dependency set:

- pyyaml for config
- pytest for tests
- stdlib urllib for http

## repo tone

this is a working repo, not a pitch deck.

lowercase is fine. short notes are fine. commits can describe what actually happened instead of following conventional commits religiously.

slightly messy is fine. fake mess is not.

## later maybe

- tcp checks
- docker
- api
- metrics
- tiny web view
- actual homelab integration

only when there is a reason.