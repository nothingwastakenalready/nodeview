# email delivery

## status

local development delivery is documented and wired through mailpit. account
verification and newsletter double opt-in are wired to the auth store and mail
boundary. newsletter unsubscribe persistence remains the next application
slice.

## environments

### local development

compose starts mailpit next to raffael:

```text
smtp inside docker: mailpit:1025
inbox: http://127.0.0.1:8025
```

mailpit accepts messages without delivering them to real recipients. this keeps
registration tests and UI work safe without a domain or external credentials.

for lan access, set `RAFFAEL_MAILPIT_BIND_ADDRESS` in `.env` to the docker host's
lan ip. the app's email links should use the same address through
`RAFFAEL_PUBLIC_URL`.

```env
RAFFAEL_MAILPIT_BIND_ADDRESS=192.168.1.50
RAFFAEL_PUBLIC_URL=http://192.168.1.50:8080
```

### production

proton smtp submission is the intended first production adapter when a paid
proton plan and custom domain are available:

```env
RAFFAEL_MAIL_PROVIDER=smtp
RAFFAEL_SMTP_HOST=smtp.protonmail.ch
RAFFAEL_SMTP_PORT=587
RAFFAEL_SMTP_SECURITY=starttls
RAFFAEL_SMTP_USERNAME=notifications@example.org
RAFFAEL_SMTP_PASSWORD=<smtp-token>
RAFFAEL_MAIL_FROM=notifications@example.org
RAFFAEL_PUBLIC_URL=https://monitor.example.org
```

`RAFFAEL_SMTP_PASSWORD` is a proton smtp token, not the proton account
password. it belongs in a secret store or an untracked environment file and
must never be committed.

## message flows

registration confirmation and newsletter subscription are separate flows:

1. registration creates an unverified account;
2. a short-lived, single-use confirmation token is sent;
3. account confirmation marks the address verified;
4. newsletter opt-in is explicit and separate;
5. newsletter double opt-in creates a separate subscription record;
6. every newsletter contains an immediate unsubscribe link.

an account must not be subscribed to the newsletter merely because it was
created. consent text, timestamp and subscription state must be retained for
the consent record.

## message design

transactional messages share a deliberately minimal black canvas: the centered
raffael mark, one lowercase heading and one underlined action. the logo is
served as a transparent png because svg images are not rendered consistently
by email clients. recipient addresses and account details are intentionally
omitted from the html body. until the public product descriptor is settled,
the templates do not append a tagline or infrastructure label.

## local verification flow

when `RAFFAEL_MAIL_PROVIDER=mailpit`, registration sends the confirmation
message to mailpit instead of a real recipient. open the message in the local
inbox and follow the confirmation link. the account token is single-use and
expires after 24 hours. newsletter confirmation tokens expire after 48 hours.
