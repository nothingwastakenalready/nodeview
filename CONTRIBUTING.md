# contributing

raffael is still early. useful help is welcome, but the project is not trying
to become a huge monitoring platform overnight.

## before opening work

- read `README.md`
- run it once locally
- check open issues
- keep changes small enough to review

if a change touches security, auth, network scanning or secrets, open an issue
first. monitoring software can accidentally become a port scanner with a pretty
face.

## local setup

```bash
python -m pip install -e '.[test]'
pytest

cd web
npm install
npm test
npm run build
```

docker should also keep working:

```bash
docker compose up -d --build
```

## pull requests

good pull requests usually include:

- what changed
- why it changed
- how it was tested
- screenshots for ui changes
- notes about security impact when network targets, auth or secrets are involved

please do not mix formatting sweeps with feature work.

## style

the docs are intentionally plain and lowercase. keep that thread unless there
is a good reason not to.

the app should stay boring to operate. if a feature needs a complicated setup,
document the boring path first.
