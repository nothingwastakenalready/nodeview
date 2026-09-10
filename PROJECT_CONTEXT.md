# nodeview project context

Read this first when continuing nodeview in a new session.

## what this is

NodeView is becoming a self-hosted, open-source infrastructure monitoring and observability application. It started as a small Python HTTP/TCP checker. Do not rewrite the working core just to make the project look bigger.

The product should answer quickly:

1. what is broken?
2. what is getting worse?
3. what is probably causing it?

The long-term product is multi-user and workspace-based, with a web UI and later a desktop client and remote agents.

## visual/product decisions already made

- primary infrastructure overview: hexagonal nodes
- dark/restrained interface
- monitoring color spectrum: healthy / warning / critical / unknown / pending
- similar semantic spectrum to Checkmk is fine; do not copy Checkmk UI one-to-one
- each node should show current health and latency at a glance
- latency is a first-class metric and gets history graphs
- node detail later includes services, events, uptime, latency history and agent telemetry
- dependency/topology graph is a core future feature
- dependency state can mark downstream systems `affected`; do not claim causal certainty
- status must remain understandable without color alone

## reference products

- Checkmk: host/service model, dense state overview, status semantics
- Uptime Kuma: low-friction onboarding/self-hosting
- Prometheus: time-series/metrics interoperability, not something to clone
- Gatus: simple active-check/threshold mental model
- Beszel/Netdata: hub + agent and host telemetry direction

NodeView should combine useful ideas without becoming a clone of any of them.

## data model direction

Use a workspace-first model:

user -> membership -> workspace -> nodes -> services -> checks -> measurements/events

Dependencies connect nodes/services. All tenant-owned data belongs to exactly one workspace. Roles are initially owner/admin/member/viewer.

Multi-user is planned early enough that tenant isolation does not become a retrofit across the whole codebase.

## security decisions

Security is a parallel workstream, not a final polish step.

Important boundaries:

- server-side authorization for every workspace-owned object
- explicit cross-workspace regression tests
- local auth direction: Argon2id password hashing + server-side sessions + Secure/HttpOnly/SameSite cookies
- CSRF/session rotation/revocation/rate limiting where applicable
- OIDC/OAuth and 2FA later
- monitoring creates an inherent SSRF/egress risk because users choose network targets
- trusted self-hosted mode may allow private networks; hosted/untrusted mode needs strict egress/target policy
- account for redirects, DNS rebinding, loopback, link-local and metadata endpoints
- no arbitrary remote command execution in the agent design
- least-privilege agents, authenticated enrollment, credential rotation/revocation
- secrets must not appear in examples/logs/public APIs
- desktop credentials eventually use OS credential storage

Before a serious public release: threat model, security review/pentest, security regression tests, dependency/static/secret/container scanning, SECURITY.md, private vulnerability reporting path, OpenSSF review. An independent human review is still desirable before a security-sensitive 1.0.

## technology direction

Current backend remains Python 3.11+.

Direction:

- FastAPI API
- Pydantic at boundaries
- SQLAlchemy + Alembic once persistence arrives
- SQLite for easy small/development installs where appropriate
- PostgreSQL for serious multi-user deployments
- pytest / TDD for behavior changes
- Docker Compose first-class deployment

Frontend later:

- TypeScript
- React
- Vite
- dedicated chart library for time series
- topology graph library chosen only after interaction requirements are specified

Desktop later:

- Tauri 2 direction
- reuse web frontend
- first desktop mode connects to an existing NodeView server; do not bundle the whole backend initially

## development order

Detailed roadmap: `docs/architecture/roadmap.md`.

Immediate sequence:

1. v0.2 always-on API + Docker
2. v0.3 scheduler/state engine
3. v0.4 persistence/history/latency
4. v0.5 first real web UI
5. v0.6 accounts/workspaces/tenant isolation
6. v0.7 hexagonal node view
7. v0.8 dependency graph
8. v0.9 agent
9. alerting/operations
10. Prometheus/interoperability
11. desktop client
12. 1.0 open-source hardening/release quality

Do not jump directly to pretty topology before the monitoring state engine/history are trustworthy.

## current state — 2026-09-10

v0.2 has been implemented on main: FastAPI endpoints, shared HTTP/TCP dispatcher, Dockerfile, Compose, API tests and a Docker-build CI job are present. The next product slice after v0.2 verification is the v0.3 scheduler/state engine; write its focused design spec before implementation.

v0.2 remains trusted/private-network only. Compose binds to `127.0.0.1:8080` by default because there is no auth yet. No database, scheduler, accounts or web dashboard belong to v0.2.

## working method

For substantial slices:

1. focused design spec
2. implementation plan
3. TDD: test -> observe RED -> minimal implementation -> GREEN -> refactor
4. fresh verification
5. CI
6. security impact review
7. docs
8. coherent version/release

Keep commits human and slightly dry/understated. Avoid marketing language and fake activity. The code should be technically clean even if the repo voice is a little loose.

## canonical docs

- `PROJECT_CONTEXT.md` — fast handoff/current decisions
- `docs/architecture/product-vision.md` — long-term architecture/product/security direction
- `docs/architecture/roadmap.md` — staged development streams
- `docs/superpowers/specs/2026-09-10-nodeview-v0.2-design.md` — v0.2 design

If a future conversation is missing context, read these files before proposing architecture changes.
