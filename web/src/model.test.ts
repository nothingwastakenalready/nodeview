import { describe, expect, test } from "vitest";

import { presentState, summarizeStates, type ServiceState } from "./model";

const base: ServiceState = {
  name: "dns",
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
    expect(presentState(base)).toMatchObject({
      label: "healthy",
      tone: "healthy",
      latency: "12 ms"
    });

    expect(presentState({ ...base, status: "critical", latency_ms: null })).toMatchObject({
      label: "critical",
      tone: "critical",
      latency: "—"
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
