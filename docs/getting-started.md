# getting started

If you found this repo and want to make it work: nice. This is the short path.

Raffael is a small self-hosted monitoring app. It runs locally with Docker,
stores its data in a Docker volume, and uses Mailpit for safe local email.
Mailpit catches account and password-reset emails without sending anything to
the real internet.

## what you need

- Git
- Docker Desktop, or Docker Engine with Docker Compose
- a browser

You do not need a domain, a real mail account or a public server.

## start it

```bash
git clone https://github.com/nothingwastakenalready/raffael.git
cd raffael
cp .env.example .env
cp services.example.yaml services.yaml
docker compose up -d --build
```

Open:

```text
http://127.0.0.1:8080
```

Mailpit is here:

```text
http://127.0.0.1:8025
```

## create the first account

Open Raffael and create the first account.

Only the first self-registration is expected for a normal local install.
After that, registration is closed by default so extra accounts are not created
accidentally.

If Raffael sends a confirmation or reset email, open Mailpit and use the newest
message:

```text
http://127.0.0.1:8025
```

## add a first sensor

In the dashboard, add a sensor under `active checks`.

Good first checks:

```text
type: http
url:  https://example.com
```

or:

```text
type: tcp
host: 192.168.1.1
port: 80
```

Use addresses from your own network. Raffael is intentionally conservative about
what targets it will check.

## make it visible in your LAN

For normal testing, keep the default localhost config.

If you want to open Raffael from another device in the same home network, edit
`.env` and replace `127.0.0.1` with the IP address of the machine running
Docker.

Example:

```env
RAFFAEL_BIND_ADDRESS=192.168.1.50
RAFFAEL_MAILPIT_BIND_ADDRESS=192.168.1.50
RAFFAEL_PUBLIC_URL=http://192.168.1.50:8080
```

Then restart:

```bash
docker compose up -d
```

Open:

```text
http://192.168.1.50:8080
http://192.168.1.50:8025
```

Do not expose this directly to the public internet.

## stop it

```bash
docker compose down
```

This stops the containers. The SQLite database stays in the Docker volume.

To remove the data too:

```bash
docker compose down -v
```

Only run that if you really want a fresh install.

## what works today

- local account login
- password reset through Mailpit
- HTTP checks
- TCP checks
- automatic TCP port discovery checks created from known devices
- current status
- latency
- uptime and downtime percentages from history
- durable history in SQLite
- dashboard with the starfield/constellation UI

## what is not there yet

- full Zabbix or Checkmk feature depth
- native Proxmox metrics
- native UniFi metrics
- SNMP polling
- Docker container monitoring
- ICMP ping as a first-class check
- alerting
- public internet deployment guidance
