# nodeview ui direction

This is the current design handoff for the browser interface.

## product posture

NodeView should look like a real internal infrastructure tool, not a landing page and not a generic admin template.

The interface mixes two densities:

- **overview:** compact and operational, closer to Checkmk in how much can be scanned at once
- **detail:** more spacious and modern, with room for latency/history and later telemetry

The rule is simple: dense where operators need orientation, quiet where they need analysis.

## hierarchy

1. overview
2. topology / dependency view
3. node detail

The current implementation only ships the overview plus a lightweight selected-monitor detail panel.

## overview

The primary visual motif is a field of hexagonal status tiles.

Each tile currently shows:

- service name
- current latency
- readable status
- status ring/color

The inside remains dark. Status lives mostly on the perimeter so a large grid does not become a wall of saturated color.

Target desktop density is roughly 15–25 useful tiles on a 1440p display once the real node model exists. Do not cram CPU, RAM, uptime, service counts and every secondary metric into the overview tile.

## status semantics

- healthy — green
- warning — amber
- critical — red
- unknown — grey
- pending — blue

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

## topology direction

The later topology screen sits between overview and detail in density.

It should show real dependencies, not decorative lines. Expected semantics:

- node/service relationships
- upstream/downstream direction
- direct failures as `critical`
- downstream impact as `affected` when appropriate

Never imply proven root cause when the system only knows dependency relationships.

## current implementation limitation

As of the first UI shell, the backend has services/checks but does not yet have the final workspace/node/service hierarchy.

Therefore each service is temporarily rendered as one hexagon.

Do not build product logic around that shortcut. The intended model remains:

`user -> membership -> workspace -> nodes -> services -> checks -> measurements/events`

The overview should migrate from service tiles to node tiles once that backend model is introduced.

## visual rules

- dark neutral background, not pure black
- restrained borders and surfaces
- no gratuitous gradients
- no cyberpunk/neon treatment
- no fake terminal styling
- no glassmorphism just because it exists
- no giant marketing headlines inside the product
- numbers get stronger visual weight than metadata
- typography stays clean, small and technical
- motion stays subtle and respects reduced-motion preferences

## copy

Copy stays short and dry.

Good:

- `current state`
- `last checked`
- `nothing configured yet.`
- `history lands with persistence.`

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

Before adding topology or historical charts, wait until the corresponding backend data is real.
