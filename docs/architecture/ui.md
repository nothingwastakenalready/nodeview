# raffael ui direction

This is the current design handoff for the browser interface.

## product posture

Raffael should look like a real internal infrastructure tool, not a landing page and not a generic admin template.

Raffael is not a Checkmk clone.

Checkmk is only one reference for dense operational scanning and host/service status semantics. The visual language should draw more broadly from monitoring, observability, infrastructure visualizers and modern technical tools.

Useful references by category:

- Checkmk: dense status scanning, host/service mental model, operational seriousness
- Uptime Kuma / Gatus: low-friction uptime monitoring, clear service states, simple setup
- Beszel / Netdata: lightweight host telemetry, calm server-health dashboards, hub + agent direction
- Grafana / Datadog / New Relic: dashboards, time-series reading, filtering, drill-down, incident context
- Honeycomb / SigNoz-style observability tools: event-first investigation, high-cardinality exploration, trace-like navigation ideas later
- Docker and infrastructure visualizers: live topology, container/network relationships, object maps
- Linear / Vercel / Raycast / modern developer tools: sharp typography, command-oriented polish and low visual noise

The goal is a distinct Raffael identity: technical, restrained, fast to read, slightly opinionated, and not visually owned by any one existing product.

## design principles

1. status first, decoration second
2. latency is not a secondary footnote
3. topology is explanatory, not ornamental
4. overview is for orientation; detail is for thinking
5. never use fake data just to make the UI look fuller
6. do not copy another product's layout, colors or component shapes one-to-one
7. keep the interface calm until something actually needs attention

## density model

The interface mixes two densities:

- **overview:** compact and operational, enough objects visible to scan quickly
- **detail:** more spacious and modern, with room for latency/history and later telemetry

The rule is simple: dense where operators need orientation, quiet where they need analysis.

## hierarchy

1. overview
2. topology / dependency view
3. node detail

The current implementation only ships the overview plus a lightweight selected-monitor detail panel.

## overview

The primary visual motif is a field of hexagonal status tiles for now, but the hexagon is not sacred. It is a current motif, not a prison.

Each tile currently shows:

- service name
- current latency
- readable status
- status ring/color

The inside remains quiet. Status lives mostly on the perimeter so a large grid does not become a wall of saturated color.

Target desktop density is roughly 15–25 useful tiles on a 1440p display once the real node model exists. Do not cram CPU, RAM, uptime, service counts and every secondary metric into the overview tile.

If another visual primitive later communicates state better than hexagons, it can replace them. The product requirement is fast state recognition, not geometric loyalty.

## status semantics

- healthy — green
- warning — amber
- critical — red
- unknown — grey
- pending — blue
- affected — later topology-derived downstream impact, visually distinct from direct critical failure

Exact color values are not sacred yet. Semantics are.

Color must not be the only state indicator. Status text/symbols remain visible for accessibility and fast interpretation.

## detail direction

Detail views should be noticeably calmer than the overview.

Future node detail is expected to have:

- current health
- current latency
- availability
- latency history
- services/checks
- events
- later CPU/RAM/disk/agent telemetry

Time-series charts get real space instead of being squeezed into cards for dashboard aesthetics.

Charts should be readable before they are pretty. Borrow from Grafana/Datadog/New Relic only at the pattern level: clear axes, useful ranges, good drill-down, obvious correlation. Do not build a generic dashboard-builder clone.

## topology direction

The later topology screen sits between overview and detail in density.

It should show real dependencies, not decorative lines. Expected semantics:

- node/service relationships
- upstream/downstream direction
- direct failures as `critical`
- downstream impact as `affected` when appropriate

Never imply proven root cause when the system only knows dependency relationships.

Topology should feel more like an infrastructure map than a cyberpunk poster. Lines should explain paths, blast radius and probable impact. Animation is useful only if it reveals freshness or flow.

## current implementation limitation

As of the first UI shell, the backend has services/checks but does not yet have the final workspace/node/service hierarchy.

Therefore each service is temporarily rendered as one hexagon.

Do not build product logic around that shortcut. The intended model remains:

`user -> membership -> workspace -> nodes -> services -> checks -> measurements/events`

The overview should migrate from service tiles to node tiles once that backend model is introduced.

## visual rules

- light warm-neutral application background; avoid sterile pure white across the whole canvas
- restrained borders and surfaces
- dark mode may follow later, but the light system is the current design target
- avoid copying Checkmk's exact palette, density, iconography or spacing
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

The first visual pass now follows a dark operations-console direction inspired by
modular technical dashboards and compact diagnostic widgets. This is a Raffael
direction, not a copy of any reference product.

- near-black canvas with a restrained dotted field
- modular widgets with quiet borders and compact radii
- warm white typography with orange for attention and red for critical state
- technical monospace typography for numbers, labels and system copy
- small dot meters and signal marks only where they represent a real value or
  a clearly labelled visual summary
- login uses the same dark system, with a grid field, an orange accent and a
  focused split layout

The overview keeps the existing service state and latency logic. New widgets
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

No component framework is intentionally used yet. The interface is still small and the design language is expected to evolve in Codex.

The production build is served from the same FastAPI process as the API. Development can use Vite with API proxying.

## what to improve in Codex next

Design iteration can change spacing, typography, exact colors, hexagon geometry, responsive behavior and detail composition freely as long as these product semantics survive:

- overview remains fast to scan
- current status and latency remain immediately visible
- status is understandable without color alone
- detail is calmer than overview
- no fake metrics are introduced
- current service-as-tile representation is understood as temporary
- the result feels like Raffael, not Checkmk wearing different CSS

Before adding topology or historical charts, wait until the corresponding backend data is real.
