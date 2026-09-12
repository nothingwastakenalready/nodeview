# raffael project context

Read this first when continuing raffael in a new session.

## what this is

Raffael is becoming a self-hosted, open-source infrastructure monitoring and observability application. It started as a small Python HTTP/TCP checker. Do not rewrite the working core just to make the project look bigger.

The product should answer quickly:

1. what is broken?
2. what is getting worse?
3. what is probably causing it?

The long-term product is multi-user and workspace-based, with a browser UI and later a desktop client and remote agents.

## visual/product decisions already made

- Raffael must not become a Checkmk clone
- Checkmk is only one reference for dense operational scanning and host/service status semantics
- broader visual inspiration should also come from Uptime Kuma, Gatus, Beszel, Netdata, Grafana, Datadog, New Relic, Honeycomb/SigNoz-style observability tools, Docker/infrastructure visualizers and modern developer tools like Linear/Vercel/Raycast
- primary infrastructure overview currently uses hexagonal tiles, but the hexagon is a motif, not a permanent constraint
- light, calm application canvas with restrained technical surfaces; dark mode can follow later
- density model: overview is compact, topology medium-density, detail spacious
- monitoring color spectrum: healthy / warning / critical / unknown / pending, with later `affected` for topology-derived downstream impact
- do not copy any product's exact layout, colors, icons, spacing or component shapes one-to-one
- quiet tile interiors with stronger status perimeter/ring are preferred over fully saturated tiles
- status must remain understandable without color alone
- current health and latency should be visible at a glance
- latency is a first-class metric and gets history graphs once persistence exists
- node detail later includes services, events, uptime, latency history and agent telemetry
- dependency/topology graph is a core future feature
- dependency state can mark downstream systems `affected`; do not claim causal certainty
- UI should feel like a real internal infrastructure tool, not a landing page, fake terminal, cyberpunk poster or generic admin template
- repo/UI copy stays short, dry and functional

## UI identity target

Raffael should feel technical, restrained, fast to read, slightly opinionated and self-hosted-native.

The first UI shell is allowed to be imperfect. Its job is to make the running monitor visible. Future UI work should create a distinct Raffael design language rather than polishing the current shell into a Checkmk-adjacent clone.

Core UI principles:

1. status first, decoration second
2. latency is not a secondary footnote
3. topology is explanatory, not ornamental
4. overview is for orientation; detail is for thinking
5. never use fake data just to make the UI look fuller
6. keep the interface calm until something actually needs attention

## reference products

- Checkmk: host/service model, dense state overview, status semantics
- Uptime Kuma: low-friction onboarding/self-hosting, clear uptime status feel
- Gatus: simple active-check/threshold mental model, config-as-code health checks
- Beszel/Netdata: lightweight host telemetry, calm server-health dashboards, hub + agent direction
- Grafana: time-series/dashboard reading patterns and composable visual panels, not a thing to clone
- Datadog/New Relic: drill-down, incident context, correlation and dashboard interaction patterns
- Honeycomb/SigNoz-style tools: event-first investigation and later observability navigation ideas
- Docker/infrastructure visualizers: live topology and object relationship maps
- Linear/Vercel/Raycast-style developer tools: restrained modern technical polish and low visual noise

Raffael should combine useful ideas without becoming a clone of any of them.

## data model direction

Use a workspace-first model:

user -> membership -> workspace -> nodes -> services -> checks -> measurements/events

Dependencies connect nodes/services. All tenant-owned data belongs to exactly one workspace. Roles are initially owner/admin/member/viewer.

Multi-user is planned early enough that tenant isolation does not become a retrofit across the whole codebase.

Important current UI limitation: v0.3 does not yet have the final node/workspace model, so the first browser UI temporarily renders each monitored service as one overview hexagon. Do not build product logic around that shortcut. Migrate overview tiles to real nodes once the backend model exists.

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

Continuous scheduling increases the importance of SSRF/egress controls because configured targets are contacted repeatedly. Until target-policy hardening and auth/tenant isolation exist, Raffael remains trusted/self-hosted and should not be exposed to untrusted users.

Before a serious public release: threat model, security review/pentest, security regression tests, dependency/static/secret/container scanning, SECURITY.md, private vulnerability reporting path, OpenSSF review. An independent human review is still desirable before a security-sensitive 1.0.

## technology direction

Backend:

- Python 3.11+
- FastAPI API
- asyncio in-process scheduler for the current single-server architecture
- synchronous protocol checks executed through `asyncio.to_thread()` so they do not block the event loop
- Pydantic at boundaries
- SQLAlchemy + Alembic once persistence arrives
- SQLite for easy small/development installs where appropriate
- PostgreSQL for serious multi-user deployments
- pytest / TDD for behavior changes
- Docker Compose first-class deployment

Frontend now exists as a deliberately small shell:

- React 19.3
- TypeScript
- Vite 8.x
- Vitest 5
- plain CSS for now
- same-origin production deployment: frontend is compiled in Docker and served by FastAPI
- local design iteration can use the Vite dev server with API proxying
- no component framework yet because the visual language is still expected to evolve in Codex

Frontend later:

- dedicated chart library for time series
- topology graph library chosen only after interaction requirements are specified

Desktop later:

- Tauri 2 direction
- reuse web frontend
- first desktop mode connects to an existing Raffael server; do not bundle the whole backend initially

## development order

Detailed roadmap: `docs/architecture/roadmap.md`.

Immediate sequence:

1. v0.2 always-on API + Docker — implemented
2. v0.3 scheduler/state engine — implemented
3. first browser UI shell — implemented after v0.3, intentionally before persistence so the project can be inspected locally
4. v0.4 persistence/history/latency — in progress; durable measurements and history API implemented first
5. proper node/workspace model + richer web UI
6. accounts/workspaces/tenant isolation
7. real node overview with its own visual language
8. dependency graph
9. agent
10. alerting/operations
11. Prometheus/interoperability
12. desktop client
13. 1.0 open-source hardening/release quality

Do not jump directly to pretty topology before the monitoring state engine/history and real dependency data are trustworthy.

## current state — 2026-09-12

Raffael replaces the former project name across product, package, API and documentation. v0.4 has started on top of the v0.3 monitoring engine.

Implemented backend behavior:

- existing HTTP/TCP checks remain the protocol core
- each configured service can define `interval`, `failure_threshold`, and `success_threshold`
- defaults: 30 second interval, 2 failures to become critical, 1 success to recover
- services start in `pending`
- successful checks become `up`
- failures before the configured failure threshold become `warning`
- threshold-reaching failures become `critical`
- unexpected checker/engine exceptions become `unknown` instead of killing the scheduler
- recovery can require multiple consecutive successes
- success/failure counters reset each other
- each service has an asyncio scheduling loop
- synchronous checks run via `asyncio.to_thread()`
- a shared semaphore bounds concurrent checks; default max concurrency is 10
- engine start avoids duplicate service loops
- engine stop cancels and awaits scheduler tasks cleanly
- FastAPI lifespan starts/stops the default engine
- `GET /state` exposes the current in-memory state
- `/health`, `/services`, and `/check` keep their earlier meanings

First browser UI shell:

- compact first dashboard shell; a light redesign is now the target
- summary counts for healthy/warning/critical/unknown/pending
- hexagonal overview tiles showing service name, current latency and readable status
- selected-service detail with last check, HTTP status, streak counters and last error
- 5-second `/state` refresh
- loading, empty, stale/error states
- accessible button semantics, focus state and reduced-motion support
- frontend unit/render tests in CI
- production frontend compiled through a Node Docker stage and served from the same FastAPI container
- Compose remains a single service and localhost-only by default

Current operational state remains intentionally in-memory and resets to pending after restart. Scheduled check measurements now persist in SQLite through a SQLAlchemy boundary, with an initial Alembic migration and bounded UTC time-range API. There is no uptime calculation, retention job, state-change event table, alerting, authentication, final node/workspace model or dependency topology yet.

The browser UI now has a dark modular operations-console direction. It uses live-derived overview widgets for healthy percentage, attention count and selected latency, plus the existing service status overview and detail panel. A login page exists as a visual route at `#/login`; it does not claim successful authentication until the backend auth slice is connected.

The first backend auth slice now provides local registration, Argon2id password hashing, server-side sessions, CSRF-protected logout, an owner membership in a default workspace, and authentication gates on service/state/history reads when database-backed auth is enabled. YAML monitor configuration is still shared self-hosted data rather than independently workspace-owned; a later model must add explicit workspace ownership before recommending internet-facing multi-tenant deployment.

The remaining v0.4 work is state-change events, retention and uptime calculation. Keep the slice narrow; Raffael is not a general-purpose TSDB.

## local inspection

The intended local flow is:

```bash
git clone https://github.com/nothingwastakenalready/raffael.git
cd raffael
cp services.example.yaml services.yaml
docker compose up -d --build
```

Open `http://127.0.0.1:8080`.

For UI iteration in Codex/local dev, run the backend on port 8080 and then `cd web && npm install && npm run dev`.

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
- `docs/architecture/ui.md` — current UI direction and Codex handoff
- `docs/superpowers/specs/2026-09-10-raffael-v0.2-design.md` — v0.2 design
- `docs/superpowers/specs/2026-09-11-raffael-v0.3-design.md` — scheduler/state-engine design
- `docs/superpowers/plans/2026-09-11-raffael-v0.3.md` — v0.3 implementation plan
- `docs/superpowers/specs/2026-09-11-raffael-ui-shell-design.md` — first browser UI shell design
- `docs/superpowers/plans/2026-09-11-raffael-ui-shell.md` — UI shell implementation plan

If a future conversation is missing context, read these files before proposing architecture changes.
