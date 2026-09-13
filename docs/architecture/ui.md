# raffael ui direction

this is the current design handoff for the browser interface.

## product posture

raffael should look like a real internal infrastructure tool, not a landing page and not a generic admin template.

raffael is not a checkmk clone.

checkmk is only one reference for dense operational scanning and host/service status semantics. the visual language should draw more broadly from monitoring, observability, infrastructure visualizers and modern technical tools.

useful references by category:

- checkmk: dense status scanning, host/service mental model, operational seriousness
- uptime kuma / gatus: low-friction uptime monitoring, clear service states, simple setup
- beszel / netdata: lightweight host telemetry, calm server-health dashboards, hub + agent direction
- grafana / datadog / new relic: dashboards, time-series reading, filtering, drill-down, incident context
- honeycomb / signoz-style observability tools: event-first investigation, high-cardinality exploration, trace-like navigation ideas later
- docker and infrastructure visualizers: live topology, container/network relationships, object maps
- linear / vercel / raycast / modern developer tools: sharp typography, command-oriented polish and low visual noise

the goal is a distinct raffael identity: technical, restrained, fast to read, slightly opinionated, and not visually owned by any one existing product.

## design principles

1. status first, decoration second
2. latency is not a secondary footnote
3. topology is explanatory, not ornamental
4. overview is for orientation; detail is for thinking
5. never use fake data just to make the UI look fuller
6. do not copy another product's layout, colors or component shapes one-to-one
7. keep the interface calm until something actually needs attention

## density model

the interface mixes two densities:

- **overview:** compact and operational, enough objects visible to scan quickly
- **detail:** more spacious and modern, with room for latency/history and later telemetry

the rule is simple: dense where operators need orientation, quiet where they need analysis.

## hierarchy

1. overview
2. topology / dependency view
3. node detail

the current implementation only ships the overview plus a lightweight selected-monitor detail panel.

## overview

the primary visual motif is a field of hexagonal status tiles for now, but the hexagon is not sacred. it is a current motif, not a prison.

each tile currently shows:

- service name
- current latency
- readable status
- status ring/color

the inside remains quiet. status lives mostly on the perimeter so a large grid does not become a wall of saturated color.

target desktop density is roughly 15-25 useful tiles on a 1440p display once the real node model exists. do not cram cpu, ram, uptime, service counts and every secondary metric into the overview tile.

if another visual primitive later communicates state better than hexagons, it can replace them. the product requirement is fast state recognition, not geometric loyalty.

## status semantics

- healthy - green
- warning - amber
- critical - red
- unknown - grey
- pending - blue
- affected - later topology-derived downstream impact, visually distinct from direct critical failure

exact color values are not sacred yet. semantics are.

color must not be the only state indicator. status text/symbols remain visible for accessibility and fast interpretation.

## detail direction

detail views should be noticeably calmer than the overview.

future node detail is expected to have:

- current health
- current latency
- availability
- latency history
- services/checks
- events
- later cpu/ram/disk/agent telemetry

time-series charts get real space instead of being squeezed into cards for dashboard aesthetics.

charts should be readable before they are pretty. borrow from grafana/datadog/new relic only at the pattern level: clear axes, useful ranges, good drill-down, obvious correlation. do not build a generic dashboard-builder clone.

## topology direction

the later topology screen sits between overview and detail in density.

it should show real dependencies, not decorative lines. expected semantics:

- node/service relationships
- upstream/downstream direction
- direct failures as `critical`
- downstream impact as `affected` when appropriate

never imply proven root cause when the system only knows dependency relationships.

topology should feel more like an infrastructure map than a cyberpunk poster. lines should explain paths, blast radius and probable impact. animation is useful only if it reveals freshness or flow.

## current implementation limitation

as of the first UI shell, the backend has services/checks but does not yet have the final workspace/node/service hierarchy.

therefore each service is temporarily rendered as one hexagon.

do not build product logic around that shortcut. the intended model remains:

`user -> membership -> workspace -> nodes -> services -> checks -> measurements/events`

the overview should migrate from service tiles to node tiles once that backend model is introduced.

## visual rules

- light warm-neutral application background; avoid sterile pure white across the whole canvas
- restrained borders and surfaces
- dark mode may follow later, but the light system is the current design target
- avoid copying checkmk's exact palette, density, iconography or spacing
- no gratuitous gradients
- no cyberpunk/neon treatment as the default identity
- no fake terminal styling
- no glassmorphism just because it exists
- no giant marketing headlines inside the product
- numbers get stronger visual weight than metadata
- typography stays clean, small and technical
- motion stays subtle and respects reduced-motion preferences
- accents can be sharper and more ownable than today, but must support state clarity

## current visual direction (2026-09-12)

the first visual pass now follows a dark operations-console direction inspired by
modular technical dashboards and compact diagnostic widgets. this is a raffael
direction, not a copy of any reference product.

- near-black canvas with a restrained dotted field
- modular widgets with quiet borders and compact radii
- warm white typography with orange for attention and red for critical state
- technical monospace typography for numbers, labels and system copy
- small dot meters and signal marks only where they represent a real value or
  a clearly labelled visual summary
- login uses the same dark system, with a grid field, an orange accent and a
  focused split layout

the overview keeps the existing service state and latency logic. new widgets
derive only from live state: healthy percentage, warning/critical count and the
selected monitor latency. No illustrative metrics are presented as real data.

## copy

Copy stays short and dry.

Good:

- `current state`
- `last checked`
- `nothing configured yet.`
- `history is recording.`

Avoid:

- `Welcome to your powerful monitoring experience`
- `Unlock actionable insights`
- `Your infrastructure, reimagined`

## frontend structure

Current first-shell stack:

- React 19.3
- TypeScript
- Vite 8.x
- Vitest 5
- plain CSS

no component framework is intentionally used yet. the interface is still small and the design language is expected to evolve in codex.

the production build is served from the same fastapi process as the api. development can use vite with api proxying.

## what to improve in Codex next

Design iteration can change spacing, typography, exact colors, hexagon geometry, responsive behavior and detail composition freely as long as these product semantics survive:

- overview remains fast to scan
- current status and latency remain immediately visible
- status is understandable without color alone
- detail is calmer than overview
- no fake metrics are introduced
- current service-as-tile representation is understood as temporary
- the result feels like raffael, not checkmk wearing different CSS

Before adding topology or historical charts, wait until the corresponding backend data is real.
