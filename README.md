# nodeview

i have too many random things running at home and got tired of checking them one by one.

so this checks them.

there are obviously a hundred tools that do this already. i didn't want any of them.

## right now

- yaml in
- http checks
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
example  UP  82ms  200
something  DOWN  connection refused
```

config is not particularly exciting either:

```yaml
services:
  - name: example
    url: https://example.com
    timeout: 2
```

`services.yaml` is ignored on purpose. i'm eventually pointing this at things that don't need to be on github.

## later

probably tcp checks, docker, an api, metrics and some kind of tiny web view.

not adding any of that until i actually want it.

## dev

```bash
python -m pip install -e '.[test]'
pytest
```

python 3.11+.
