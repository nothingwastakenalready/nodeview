# Raffael account-confirmation email

## Status

Implemented with SMTP delivery, short-lived token persistence and local
Mailpit preview.

## Design

- black Raffael canvas
- centered transparent Raffael logo
- one short confirmation action
- plain-text fallback for accessibility and mail clients
- no password, token, or account details in the message body
- no provisional product tagline

## Integration boundary

`raffael.email_templates.confirmation_email()` returns a provider-neutral
`EmailMessage` with `subject`, `text`, and `html`. The SMTP adapter can point at
Mailpit locally or a production submission service without changing the
design. Confirmation tokens are single-use, short-lived and persisted only as
digests.
