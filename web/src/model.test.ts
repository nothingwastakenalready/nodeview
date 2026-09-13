import { describe, expect, test } from "vitest";

import { presentState, summarizeStates, type ServiceState } from "./model";

const base: ServiceState = {
  name: "dns",
  check_id: null,
  workspace_id: null,
  device_id: null,
  status: "up",
  latency_ms: 12,
  http_status: null,
  error: null,
  last_checked: "2026-09-11T10:00:00+00:00",
  consecutive_successes: 4,
  consecutive_failures: 0
};

describe("state presentation", () => {
  test("maps engine state to readable status semantics", () => {
    expect(presentState({ ...base, uptime_pct: 99.5, downtime_pct: 0.5, avg_latency_ms: 14, down_events: 1 })).toMatchObject({
      label: "healthy",
      tone: "healthy",
      latency: "12 ms",
      uptime: "99.5%",
      downtime: "0.5%",
      avgLatency: "14 ms",
      downEvents: "1"
    });

    expect(presentState({ ...base, status: "critical", latency_ms: null })).toMatchObject({
      label: "critical",
      tone: "critical",
      latency: "—",
      uptime: "—"
    });
  });

  test("summarizes current states without inventing metrics", () => {
    expect(summarizeStates([
      base,
      { ...base, name: "proxy", status: "warning" },
      { ...base, name: "home", status: "critical" },
      { ...base, name: "nas", status: "pending" }
    ])).toEqual({
      total: 4,
      healthy: 1,
      warning: 1,
      critical: 1,
      unknown: 0,
      pending: 1
    });
  });
});
