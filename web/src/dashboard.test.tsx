import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, test } from "vitest";

import { Dashboard } from "./Dashboard";
import type { ServiceState } from "./model";

const states: ServiceState[] = [
  {
    name: "dns",
    status: "up",
    latency_ms: 12,
    http_status: 200,
    error: null,
    last_checked: "2026-09-11T10:00:00+00:00",
    consecutive_successes: 4,
    consecutive_failures: 0
  },
  {
    name: "proxy",
    status: "warning",
    latency_ms: 87,
    http_status: null,
    error: "slow",
    last_checked: "2026-09-11T10:00:01+00:00",
    consecutive_successes: 0,
    consecutive_failures: 1
  }
];

describe("Dashboard", () => {
  test("renders a compact overview and selected monitor detail", () => {
    const html = renderToStaticMarkup(
      <Dashboard states={states} selectedName="dns" onSelect={() => undefined} />
    );

    expect(html).toContain("system overview");
    expect(html).toContain("dns");
    expect(html).toContain("12 ms");
    expect(html).toContain("healthy");
    expect(html).toContain("last checked");
    expect(html).toContain("http 200");
  });

  test("keeps warning state readable without relying on color", () => {
    const html = renderToStaticMarkup(
      <Dashboard states={states} selectedName="proxy" onSelect={() => undefined} />
    );

    expect(html).toContain("warning");
    expect(html).toContain("slow");
  });
});
