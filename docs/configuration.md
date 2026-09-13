# configuration

Raffael is configured through environment variables. For Docker Compose, copy
the example file and edit it:

```bash
cp .env.example .env
```

The default config is private to the machine running Docker.

## network

```env
RAFFAEL_BIND_ADDRESS=127.0.0.1
RAFFAEL_MAILPIT_BIND_ADDRESS=127.0.0.1
RAFFAEL_PUBLIC_URL=http://127.0.0.1:8080
```

`RAFFAEL_BIND_ADDRESS` controls where the app is published.

`RAFFAEL_MAILPIT_BIND_ADDRESS` controls where the local Mailpit inbox is
published.

`RAFFAEL_PUBLIC_URL` is used for links in emails, especially password reset
links. If the app is opened through a LAN IP, this value must use the same LAN
address.

LAN example:

```env
RAFFAEL_BIND_ADDRESS=192.168.1.50
RAFFAEL_MAILPIT_BIND_ADDRESS=192.168.1.50
RAFFAEL_PUBLIC_URL=http://192.168.1.50:8080
```

Do not expose Raffael directly to the public internet.

## local mail

The default mail setup uses Mailpit:

```env
RAFFAEL_MAIL_PROVIDER=mailpit
RAFFAEL_SMTP_HOST=mailpit
RAFFAEL_SMTP_PORT=1025
RAFFAEL_MAIL_FROM=no-reply@localhost
```

Mailpit catches messages locally. It does not send real email.

Default inbox:

```text
http://127.0.0.1:8025
```

LAN inbox, if `RAFFAEL_MAILPIT_BIND_ADDRESS` is set to a LAN IP:

```text
http://192.168.1.50:8025
```

## production smtp

Real SMTP is optional and should use an untracked `.env` file or a secret store.

```env
RAFFAEL_MAIL_PROVIDER=smtp
RAFFAEL_SMTP_HOST=smtp.example.org
RAFFAEL_SMTP_PORT=587
RAFFAEL_SMTP_SECURITY=starttls
RAFFAEL_SMTP_USERNAME=notifications@example.org
RAFFAEL_SMTP_PASSWORD=<smtp-token>
RAFFAEL_MAIL_FROM=notifications@example.org
RAFFAEL_PUBLIC_URL=https://monitor.example.org
```

Never commit SMTP passwords, API keys or tokens.

## optional integrations

These are placeholders for current and upcoming integrations:

```env
RAFFAEL_UNIFI_URL=
RAFFAEL_UNIFI_USERNAME=
RAFFAEL_UNIFI_PASSWORD=
RAFFAEL_UNIFI_API_KEY=
RAFFAEL_UNIFI_SITE=default
RAFFAEL_UNIFI_VERIFY_TLS=1

RAFFAEL_API_CLIENTS_URL=
RAFFAEL_API_CLIENTS_TOKEN=

RAFFAEL_SNMP_TARGETS=
RAFFAEL_SNMP_COMMUNITY=public
RAFFAEL_SNMP_PORT=161
```

Leave them empty until the integration is configured.
