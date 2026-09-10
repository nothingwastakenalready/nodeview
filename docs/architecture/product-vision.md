# nodeview product vision

nodeview starts as a small health checker and grows into a self-hosted, open-source infrastructure monitoring application.

not trying to beat checkmk, prometheus, grafana, uptime kuma or netdata at their own game.

steal the good ideas, keep the shape smaller.

## product idea

nodeview should answer three questions fast:

1. what is broken?
2. what is getting worse?
3. what is probably causing it?

The primary visual language is a node map built around hexagonal infrastructure nodes, status colors and drill-down telemetry.

A node is not just a URL. It can represent a server, VM, container host, appliance, switch, logical system or remote machine.

Services and checks belong to nodes. Measurements and events belong to checks. Dependencies connect nodes and services.

```text
workspace
  |
  +-- nodes
       |
       +-- services
       |    |
       |    +-- checks
       |         |
       |         +-- measurements
       |         +-- events
       |
       +-- dependencies
```

## product surfaces

One backend, multiple clients.

```text
                       browser
                          |
                          v
                    web frontend
                          |
                          v
agent(s) -----> nodeview api/core <----- desktop app
                     |    |
                     |    +-- auth / workspaces
                     |    +-- scheduler / checks
                     |    +-- events / alerts
                     |    +-- public api
                     |
                     v
                   data
```

The desktop app should reuse the same frontend rather than becoming a second product. Tauri is the current preferred packaging direction once the web client is mature.

## visual identity

### overview

- dark, restrained interface
- hexagonal node map as the main infrastructure overview
- monitoring status spectrum similar in semantics to mature monitoring systems: healthy / warning / critical / unknown / pending
- color communicates state, not decoration
- node label + current latency available at a glance
- clusters/groups for larger environments

### node detail

A selected node opens a detail view with:

- current state
- current latency
- uptime / availability
- active services
- current problems
- recent events
- latency history
- later CPU, memory, disk, network and container telemetry

### dependency view

A graph connects infrastructure relationships so nodeview can distinguish multiple symptoms from a shared likely cause.

Example:

```text
internet
   |
gateway
 /     \
dns   proxy
 |       |
apps   services
```

Dependency state must not pretend to prove causality. It indicates affected/downstream relationships and likely root causes.

## data model

The application is workspace-first rather than user-id-everywhere.

```text
user
  |
  +-- memberships ---- workspace
                       |
                       +-- nodes
                       +-- services
                       +-- checks
                       +-- dependencies
                       +-- notification policies
                       +-- audit events
```

Roles initially:

- owner
- admin
- member
- viewer

Every tenant-owned object belongs to exactly one workspace. Authorization happens through workspace membership, never by trusting object IDs supplied by the client.

## monitoring model

### phase-one active checks

- HTTP / HTTPS
- TCP
- ICMP
- DNS

Each check can produce:

- status
- latency
- timestamp
- error category
- protocol-specific fields

Latency is a first-class metric, not display metadata.

Thresholds are check-aware and configurable. A single global `100ms = bad` rule is not useful across LAN and internet targets.

### later agent telemetry

A small nodeview agent can report host-level data such as:

- CPU
- memory
- disks/filesystems
- network throughput
- uptime/load
- temperatures where available
- processes/services
- Docker/container state

The long-term agent should be a small standalone binary with minimal privileges. The exact implementation language stays open until the server protocol is stable.

### history

Measurements are append-oriented time-series data. The product needs retention/downsampling rules before high-frequency telemetry is enabled.

Do not build a full Prometheus replacement. NodeView stores enough history for its own UX and can later expose Prometheus-compatible metrics for users who want deeper external analysis.

## security model

security is architecture, not a v1 checkbox.

### authentication

- local accounts for self-hosted installs
- passwords stored with a modern password hashing scheme (Argon2id direction)
- server-side session model using secure, HttpOnly cookies for the web client
- CSRF protection where required
- session rotation and revocation
- rate limiting on authentication endpoints
- later optional OIDC/OAuth login
- 2FA after base auth is stable

### tenant isolation

- workspace ownership on all tenant data
- authorization enforced server-side
- tests specifically attempt cross-workspace access
- no client-supplied workspace identity trusted without membership validation

### monitoring-specific SSRF risk

Monitoring intentionally makes outbound network requests, so target validation is a core security boundary.

NodeView must distinguish deployment modes:

- trusted self-hosted mode: operator can permit private networks
- hosted/multi-tenant mode: strict target policy, address resolution checks and network egress controls

Protection must account for redirects, DNS rebinding, loopback, link-local, metadata endpoints and private address ranges where the deployment policy forbids them.

### secrets

- no secrets in repository/config examples
- encrypted secret storage when integrations require credentials
- never expose internal targets/secrets through public APIs or logs
- desktop credentials use operating-system credential storage rather than plain files/localStorage

### software supply chain

Open-source releases should add:

- dependency scanning
- static analysis
- secret scanning
- container scanning
- signed/reproducible release direction
- SECURITY.md and private vulnerability reporting path
- OpenSSF Scorecard as a project-health signal

## technology direction

### backend

Keep the existing Python core.

Preferred direction:

- Python 3.11+
- FastAPI for HTTP API
- Pydantic models at API/config boundaries
- SQLAlchemy 2.x style persistence
- Alembic migrations
- SQLite for easy single-node development/small installs where feasible
- PostgreSQL as the supported serious multi-user deployment database
- pytest

Business/monitoring logic must not live inside FastAPI route functions.

### frontend

Preferred direction:

- TypeScript
- React
- Vite
- API-generated/shared types where practical
- SVG/CSS for the hex node surface
- a graph library for dependency topology only after interaction requirements are proven
- chart library for time-series data

Do not choose a huge dashboard framework just to get charts quickly.

### desktop

Tauri 2 is the preferred later wrapper for Windows/macOS/Linux because the existing web UI can be reused while native capabilities can be explicitly permission-scoped.

Desktop is not required for the first useful web release.

### deployment

First-class Docker Compose install.

Later:

- OCI images via GitHub Container Registry
- documented reverse-proxy/TLS setup
- health checks
- backup/restore
- upgrade/migration documentation
- optional Helm chart only after there is actual demand

## external inspiration

### checkmk

borrow:

- host/service mental model
- quick status perception
- severity states
- service discovery ideas later
- dense infrastructure overview

avoid:

- copying its UI directly
- enterprise configuration complexity early

### uptime kuma

borrow:

- fast onboarding
- low-friction self-hosting
- approachable monitor creation

avoid:

- remaining primarily a flat endpoint/status-page product

### prometheus

borrow:

- metrics/time-series semantics
- labels carefully where useful
- exporter/integration friendliness

avoid:

- building our own PromQL or general-purpose TSDB platform

### gatus

borrow:

- straightforward active checks
- response-time thresholds
- declarative mental model

avoid:

- config-only UX as the long-term product surface

### beszel/netdata

borrow:

- hub + agent direction
- host telemetry
- lightweight remote collection

avoid:

- turning nodeview into only another resource graph dashboard

## non-goals

- clone checkmk
- clone grafana
- become a generic log platform
- implement a custom query language early
- Kubernetes-first design
- cloud/SaaS-first design
- billing/subscriptions
- AI features because apparently everything needs AI now

## definition of success

A technically competent stranger should eventually be able to:

1. clone or pull nodeview
2. run it with Docker Compose
3. create an account
4. create a workspace
5. add infrastructure
6. see state and latency immediately
7. install an agent for deeper host telemetry
8. understand dependency impact
9. upgrade without losing data
10. inspect the source, tests and security documentation and reasonably trust what is running
