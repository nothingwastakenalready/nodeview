# email delivery

## status

Local development delivery is documented and wired through Mailpit. Account
verification and newsletter double opt-in are wired to the auth store and mail
boundary. Newsletter unsubscribe persistence remains the next application
slice.

## environments

### local development

Compose starts Mailpit next to Raffael:

```text
SMTP: 127.0.0.1:1025
Inbox: http://127.0.0.1:8025
```

Mailpit accepts messages without delivering them to real recipients. This keeps
registration tests and UI work safe without a domain or external credentials.

### production

Proton SMTP Submission is the intended first production adapter when a paid
Proton plan and custom domain are available:

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

`RAFFAEL_SMTP_PASSWORD` is a Proton SMTP token, not the Proton account
password. It belongs in a secret store or an untracked environment file and
must never be committed.

## message flows

Registration confirmation and newsletter subscription are separate flows:

1. registration creates an unverified account;
2. a short-lived, single-use confirmation token is sent;
3. account confirmation marks the address verified;
4. newsletter opt-in is explicit and separate;
5. newsletter double opt-in creates a separate subscription record;
6. every newsletter contains an immediate unsubscribe link.

An account must not be subscribed to the newsletter merely because it was
created. Consent text, timestamp and subscription state must be retained for
the consent record.

## local verification flow

When `RAFFAEL_MAIL_PROVIDER=mailpit`, registration sends the confirmation
message to Mailpit instead of a real recipient. Open the message in the local
inbox and follow the confirmation link. The account token is single-use and
expires after 24 hours. Newsletter confirmation tokens expire after 48 hours.
