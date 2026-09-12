# Raffael account-confirmation email

## Status

Prepared template only. Delivery and token persistence remain a later slice.

## Design

- black Raffael canvas
- centered Raffael logo
- one short confirmation action
- plain-text fallback for accessibility and mail clients
- no password, token, or account details in the message body

## Integration boundary

`raffael.email_templates.confirmation_email()` returns a provider-neutral
`EmailMessage` with `subject`, `text`, and `html`. A later mail adapter can use
Resend, SMTP, Postmark, or another provider without changing the design.

Before enabling delivery, add a single-use, short-lived confirmation token and
store only its digest. The confirmation endpoint must not reveal whether an
email address exists, and resend requests should be rate limited.
