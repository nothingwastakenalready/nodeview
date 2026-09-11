# NodeView UI Shell Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first production-served NodeView browser UI on top of the existing v0.3 `/state` API.

**Architecture:** A small React/TypeScript/Vite frontend lives under `web/`. It fetches monitoring state from the same-origin FastAPI API, renders a dense hexagon overview plus a spacious selected-monitor detail panel, and is built into the existing Docker image through a multi-stage build. FastAPI serves the compiled assets without changing existing API semantics.

**Tech Stack:** Python 3.11+, FastAPI, React 19.3, TypeScript, Vite 8.x, Vitest 5, Docker multi-stage build.

**Spec:** `docs/superpowers/specs/2026-09-11-nodeview-ui-shell-design.md`

## Global Constraints

- Do not invent node relationships, history, uptime, packet loss, health scores or telemetry that v0.3 does not provide.
- Existing API behavior must remain compatible.
- UI copy stays short, dry and functional.
- Production UI and API share one origin.
- Status is never conveyed by color alone.
- Keep the frontend dependency surface small.

---

### Task 1: Frontend test harness and state presentation

**Files:**
- Create: `web/package.json`
- Create: `web/tsconfig.json`
- Create: `web/vite.config.ts`
- Create: `web/src/model.test.ts`
- Create: `web/src/dashboard.test.tsx`
- Modify: `.github/workflows/test.yml`

**Interfaces:**
- Produces frontend test/build commands and expected state-to-presentation behavior.

- [ ] Write failing tests for status labels/semantic classes and rendered overview/detail content.
- [ ] Add a CI `web` job using a supported Node release.
- [ ] Run CI and observe RED because implementation files do not exist yet.

### Task 2: Minimal React UI

**Files:**
- Create: `web/index.html`
- Create: `web/src/model.ts`
- Create: `web/src/Dashboard.tsx`
- Create: `web/src/App.tsx`
- Create: `web/src/main.tsx`
- Create: `web/src/styles.css`

**Interfaces:**
- Consumes: `GET /state`
- Produces: responsive overview/detail UI.

- [ ] Implement only enough state mapping for tests to pass.
- [ ] Implement accessible hexagon buttons, overview summary and detail panel.
- [ ] Add loading, empty and API error states.
- [ ] Poll `/state` periodically.
- [ ] Run frontend tests and build GREEN.

### Task 3: Serve production frontend through FastAPI

**Files:**
- Modify: `tests/test_api.py`
- Modify: `src/nodeview/api.py`

**Interfaces:**
- `create_app(..., ui_path: str | Path | None = None)`
- `GET /` serves `index.html` when a compiled UI exists.
- `/assets/*` serves Vite assets when present.

- [ ] Write Python test first for serving a supplied UI directory.
- [ ] Observe RED.
- [ ] Add minimal static asset serving without changing API routes.
- [ ] Run backend tests GREEN.

### Task 4: Single-container production build

**Files:**
- Modify: `Dockerfile`
- Create: `web/.gitignore`

**Interfaces:**
- Node builder outputs `web/dist`.
- Python runtime receives compiled files under `/app/web/dist`.

- [ ] Add Node build stage using current supported Node.
- [ ] Keep final runtime Python-only and non-root.
- [ ] Verify Docker build in CI.

### Task 5: Documentation and handoff

**Files:**
- Modify: `README.md`
- Modify: `PROJECT_CONTEXT.md`
- Create: `docs/architecture/ui.md`

- [ ] Document how to run production UI with Compose.
- [ ] Document local web development commands.
- [ ] Record the hybrid density direction, status semantics and temporary service-as-tile limitation.
- [ ] Explicitly point future design work to the UI architecture doc and current spec.
- [ ] Run final frontend tests, frontend build, backend tests and Docker build through CI.
- [ ] Fast-forward to `main` only after all jobs are green.
