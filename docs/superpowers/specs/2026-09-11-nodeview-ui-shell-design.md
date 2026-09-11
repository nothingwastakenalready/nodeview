# nodeview ui shell design

## status

Approved direction for the first runnable NodeView UI. This is intentionally a shell on top of the existing v0.3 monitoring state, not the final node/workspace data model.

## goal

Give NodeView a useful browser interface now: dark, compact enough for operations, modern enough not to look like a legacy admin panel, and simple enough to evolve in Codex without throwing away the foundation.

## design direction

The information density is a mix of two modes:

- overview: dense, fast scanning, many monitored things visible at once
- detail: spacious, calm, room for latency/history and later telemetry

Visual hierarchy:

1. **Overview** — compact hexagonal status tiles
2. **Topology** — medium density later
3. **Detail** — spacious analysis view

The first shell implements levels 1 and a lightweight version of 3. Topology is documented but not built yet.

## visual language

- dark neutral background, not pure black
- restrained surfaces and borders
- hexagons are the main visual motif, but not decorative everywhere
- tile interior stays dark
- status is expressed primarily by a strong colored outer hexagon/ring
- status also has text/symbol semantics; color is never the only signal
- typography is clean and technical, with high-contrast numbers and quieter metadata
- no gradients, neon cyberpunk treatment, fake terminal chrome, or dashboard-template look

Status semantics:

- `up` -> healthy / green
- `warning` -> amber
- `critical` -> red
- `unknown` -> grey
- `pending` -> blue

These are semantic roles, not final brand tokens. Exact colors can be refined later.

## first screen

Desktop-first application shell:

- narrow left navigation rail
- product mark/name
- overview heading and one-line system summary
- compact responsive hexagon field
- current latency visible inside each hexagon
- current status visible by ring + label
- summary counts across healthy/warning/critical/unknown/pending
- selected monitor detail panel on the right/below depending viewport

For v0.3 data, each configured service is temporarily represented as one overview tile. Do not call this the final node model in code or docs.

## interactions

- click/focus a tile -> select it
- selected tile shows current latency, HTTP status where relevant, last checked, current error, consecutive success/failure counters
- keyboard focus should be visible
- empty state and API error state must be readable
- UI refreshes current state periodically without a full page reload

No edit/configuration workflow in this slice.

## data contract

Frontend consumes existing `GET /state` from the same origin.

Expected fields per state:

- `name`
- `status`
- `latency_ms`
- `http_status`
- `error`
- `last_checked`
- `consecutive_successes`
- `consecutive_failures`

The UI owns presentation mapping only. It must not invent health scores, uptime percentages, history, packet loss, dependency state or node relationships before backend data exists.

## frontend stack

- React 19.3
- TypeScript
- Vite 8.x
- Vitest 5
- plain CSS for the first shell

Avoid a component framework for this slice. The visual system is small enough that adding one now would constrain the later design unnecessarily.

## runtime/deployment

The production Docker image builds the frontend in a Node build stage and copies the generated assets into the Python image. FastAPI serves the built shell from the same origin as the API.

Benefits:

- one `docker compose up -d`
- no CORS setup
- no second runtime service
- later desktop client can still consume the same API independently

Development can run Vite separately when actively iterating on UI.

## testing

Frontend tests cover presentation/state mapping and rendered key semantics. Python tests cover serving the built UI shell when assets exist. CI gets a separate web job plus the existing backend and Docker build jobs.

## accessibility baseline

- status has readable text in addition to color
- interactive tiles are buttons, not clickable divs
- visible focus states
- sufficient text contrast
- reduced-motion users are not forced through decorative animation

## explicitly not in this slice

- final Node/Workspace data model
- dependency graph
- latency history chart
- authentication
- monitor editing
- notifications
- SVG export
- health score
- GitHub Pages/public demo

Those should be driven by real data and separate specs rather than mocked into the first screen.

## repo voice

Keep copy short, dry and functional. No startup language, fake customers, fake fleet statistics or marketing claims. UI labels should sound like an infrastructure tool, not a landing page.
