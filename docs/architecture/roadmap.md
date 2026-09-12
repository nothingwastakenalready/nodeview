# raffael roadmap

this is the product roadmap, not a promise to ship all of it quickly.

Each phase should leave raffael in a working state. Detailed implementation plans live separately under `docs/superpowers/plans/` immediately before execution.

## stream 0 — project foundations

Goal: make future changes cheap and reviewable.

Deliverables:

- keep HTTP/TCP core behavior stable
- shared check dispatcher
- package boundaries for monitoring/core/api later
- CI on supported Python versions
- Docker image build in CI
- architecture docs / ADRs for decisions that become hard to reverse
- security policy before accepting meaningful outside use

Exit criteria:

- tests green
- one documented runtime path
- no duplicate CLI/API monitoring logic

## stream 1 — always-on server (v0.2)

Goal: turn the CLI tool into a service.

Scope:

- FastAPI application
- `GET /health`
- `GET /services`
- `POST /check`
- shared dispatcher for HTTP/TCP
- Dockerfile
- `compose.yaml`
- API tests
- Docker build CI

Explicitly still private/trusted-network only.

Exit criteria:

- `docker compose up -d` produces a working API
- HTTP/TCP checks behave identically from CLI and API
- CI verifies Python and image build

## stream 2 — monitoring engine + scheduler (v0.3)

Goal: checks run continuously without a user request.

Scope:

- check IDs and persistent configuration model
- scheduler with bounded concurrency
- intervals and timeouts
- current-state cache/model
- state transitions (`up`, `warning`, `critical`, `unknown`, `pending`)
- failure/success thresholds to avoid flapping
- structured error categories
- graceful startup/shutdown

Do not add a UI before the engine can produce trustworthy state.

Exit criteria:

- configured checks execute on schedule
- state transitions are deterministic and tested
- restart behavior is defined

## stream 3 — persistence + history (v0.4)

Goal: answer `what changed?` rather than only `what is true right now?`.

Progress: the first v0.4 slice now stores scheduled measurements in SQLite through SQLAlchemy, ships an initial Alembic migration and exposes bounded UTC time-range history. State-change events, retention and uptime calculation remain.

Scope:

- SQLAlchemy persistence layer
- Alembic migrations
- initial SQLite development/small-install path
- PostgreSQL production/multi-user path
- measurements
- state-change events
- retention policy
- latency history
- uptime calculation
- API endpoints for history

Important design work:

- separate current state from measurement history
- avoid unbounded database growth
- define timestamp/timezone policy (UTC internally)

Exit criteria:

- restart preserves configuration/history
- migrations work from a clean database and previous schema
- latency/uptime can be queried for a time range

## stream 4 — first real web product (v0.5)

Goal: raffael becomes usable without editing YAML or reading JSON.

Scope:

- TypeScript/React/Vite frontend
- application shell/navigation
- nodes list
- services/checks list
- create/edit/delete monitor flow
- current state
- latency display
- latency history chart
- responsive desktop-first layout
- dark visual system

Hexagons start here only after basic information architecture works.

Exit criteria:

- normal monitoring setup is possible through UI
- no config file required for common use
- current state and history visible

## stream 5 — accounts + workspaces + tenant isolation (v0.6)

Goal: multiple people can use one raffael instance safely.

Data model:

- users
- workspaces
- memberships
- roles
- workspace-owned nodes/services/checks/history

Scope:

- registration/login/logout
- Argon2id password hashing
- server-side sessions
- secure/HttpOnly/SameSite cookies
- CSRF strategy
- session rotation/revocation
- login throttling/rate limiting
- authorization dependency/service
- owner/admin/member/viewer roles
- audit events for auth/privilege changes
- cross-workspace isolation tests

Security gate:

No internet-facing deployment recommendation until this stream has a dedicated security review.

Exit criteria:

- two workspaces cannot read/change each other's data
- privileged operations are role-gated
- auth lifecycle is tested

## stream 6 — the raffael visual identity (v0.7)

Goal: the interface stops looking like another CRUD monitoring dashboard.

Scope:

- hexagonal node overview
- node status spectrum
- latency in node tile
- grouping/clustering
- degraded/affected semantics
- quick filters
- node detail drawer/page
- accessibility alternatives to color-only state
- keyboard navigation where practical

Rules:

- status color has one meaning everywhere
- do not copy Checkmk geometry/layout one-to-one
- unknown/pending must not look healthy

Exit criteria:

- a problem node can be located visually within seconds
- interface remains useful with dozens of nodes
- status remains understandable without color alone

## stream 7 — topology + dependency graph (v0.8)

Goal: answer `what else is affected?`.

Scope:

- explicit dependency data model
- node/service dependency edges
- topology API
- interactive dependency graph
- downstream affected state
- root-cause candidate heuristic
- cycle detection

Important rule:

Raffael may suggest likely upstream causes but must not claim causal certainty from topology alone.

Exit criteria:

- users can model dependencies
- failures propagate as `affected` without overwriting the actual check state
- graph remains navigable on realistic small/medium homelabs

## stream 8 — raffael agent (v0.9)

Goal: go beyond outside-in reachability checks.

Protocol first, agent implementation second.

Server scope:

- agent registration/enrollment
- per-agent identity
- authenticated transport
- revocation
- heartbeat
- ingestion API/protocol
- capability/version negotiation

Agent metrics initially:

- uptime/load
- CPU
- RAM
- filesystem usage
- network counters
- basic host metadata

Then:

- Docker/container stats
- temperatures/sensors where portable
- service/process checks

Security:

- least privilege
- no arbitrary remote command execution
- explicit capability model
- rotation/revocation of enrollment credentials

Exit criteria:

- Linux host can enroll and report metrics securely
- agent loss is visible distinctly from monitored-service failure

## stream 9 — alerting + operations (v0.10)

Goal: raffael becomes useful when nobody is staring at it.

Scope:

- alert rules
- recovery notifications
- deduplication
- cooldowns
- maintenance windows
- acknowledgement
- notification destinations
- webhook first
- email later
- optional common chat integrations

Exit criteria:

- transient failures do not create alert storms
- maintenance can silence expected events
- resolved state is communicated

## stream 10 — observability interoperability (v0.11)

Goal: fit into existing infrastructure rather than replacing every tool.

Scope:

- Prometheus-compatible `/metrics`
- documented labels/naming
- API tokens/service accounts
- import/export configuration
- webhooks/events API
- optional OpenTelemetry exploration after core metrics are stable

Non-goal:

- PromQL clone
- Grafana clone

Exit criteria:

- Prometheus can scrape Raffael itself and monitor/check metrics
- third-party tools can consume stable documented data

## stream 11 — desktop application (v0.12)

Goal: package the mature web experience as a native desktop client.

Preferred direction:

- Tauri 2
- same frontend as web
- explicit capability/permission configuration
- OS credential/keychain storage for long-lived credentials
- signed builds
- updater only after release signing and CI are mature

Possible connection modes:

1. connect to an existing Raffael server
2. later evaluate bundled local server for a single-machine experience

Start with mode 1. Bundling backend/database creates a separate lifecycle problem and is not necessary initially.

Exit criteria:

- Windows/macOS/Linux client can authenticate to a server
- secrets are not stored in browser localStorage/plain files
- update path is signed/documented

## stream 12 — open-source release quality (1.0 candidate)

Goal: a stranger can safely install, understand and contribute to raffael.

Scope:

- choose/confirm license
- installation docs
- architecture docs
- backup/restore guide
- upgrade/migration guide
- reverse proxy/TLS guide
- SECURITY.md
- CONTRIBUTING.md
- CODE_OF_CONDUCT.md if community requires it
- threat model
- dependency update automation
- static/security analysis
- container vulnerability scanning
- secret scanning
- OpenSSF Scorecard review
- reproducible release process
- tagged releases + changelog
- sample configs without private addresses/secrets

Exit criteria:

- clean install works from docs
- upgrade path is tested
- security reporting path exists
- CI/release artifacts are repeatable

# parallel workstreams

Some work does not map cleanly to versions and runs continuously.

## A — security

Threat model updated whenever trust boundaries change.

Focus areas:

- authentication/session security
- tenant isolation
- SSRF/egress control
- agent enrollment
- secrets
- dependency/supply-chain security
- logging without leaking sensitive infrastructure

## B — UX/design

Maintain a small design language instead of ad-hoc components.

Focus:

- status semantics
- hex geometry
- information density
- latency/history charts
- topology interaction
- accessibility

## C — quality

- TDD for behavioral changes
- integration tests around API/database
- migration tests
- security regression tests
- UI tests for critical flows
- release smoke tests

## D — documentation/open source

Docs evolve with features rather than being written at the end.

# working method

For each stream:

1. write/approve a focused design spec
2. write a detailed implementation plan
3. implement test-first
4. run local verification
5. run CI
6. review security impact
7. update docs
8. cut a version only when the slice is actually coherent

No giant rewrite. Every stream grows the existing working product.

# immediate sequence

The next implementation sequence is:

1. finish v0.2 API + Docker as already designed
2. scheduler/state model
3. persistence/history
4. first web UI
5. accounts/workspaces
6. hexagon node view
7. dependency graph
8. agent

That order is deliberate. Pretty topology on top of an unreliable state engine is just a screensaver.
