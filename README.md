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

that's basically it.

```bash
python -m pip install -e .
cp services.example.yaml services.yaml
nodeview services.yaml
```

looks roughly like this:

```text
example  HTTP  UP  82ms  200
ssh  TCP  UP  8ms
something  TCP  DOWN  connection refused
```

config is not particularly exciting either:

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

## later

docker, an api, metrics and some kind of tiny web view probably.

not adding any of that until i actually want it.

## dev

```bash
python -m pip install -e '.[test]'
pytest
```

python 3.11+.
