# security policy

raffael monitors things by making network requests. that is useful, and also
where most of the danger lives.

## supported versions

there are no stable release lines yet. security fixes land on `main` until
real releases exist.

## report a vulnerability

please do not open a public issue for a real vulnerability.

for now, use GitHub private vulnerability reporting if it is available for this
repository. if it is not available, open a minimal public issue saying that you
have a private security report, without exploit details, target addresses,
tokens, logs or screenshots containing secrets.

include:

- what is affected
- what an attacker needs
- what happens
- reproduction steps against a local or throwaway setup
- whether credentials, workspace data or network reachability are exposed

## deployment boundary

raffael is currently meant for private/local use.

do not expose it directly to the public internet. put it behind a real reverse
proxy, tls and access control only after doing a dedicated review.

## especially sensitive areas

- ssrf and arbitrary network checks
- discovery and scan limits
- auth, sessions and csrf
- workspace isolation
- stored credentials and connector tokens
- mail/reset flows
- prometheus or debug output that might leak labels or targets
