export type EngineStatus = "up" | "warning" | "critical" | "unknown" | "pending" | string;

export interface ServiceState {
  name: string;
  check_id: number | null;
  workspace_id: number | null;
  device_id: number | null;
  status: EngineStatus;
  latency_ms: number | null;
  http_status: number | null;
  error: string | null;
  last_checked: string | null;
  consecutive_successes: number;
  consecutive_failures: number;
  availability_samples?: number;
  uptime_pct?: number | null;
  downtime_pct?: number | null;
  avg_latency_ms?: number | null;
  down_events?: number;
  details?: Record<string, string | number | boolean | null> | null;
}

export type StatusTone = "healthy" | "warning" | "critical" | "unknown" | "pending";

export interface StatePresentation {
  label: StatusTone;
  tone: StatusTone;
  latency: string;
  uptime: string;
  downtime: string;
  avgLatency: string;
  downEvents: string;
}

export interface StateSummary {
  total: number;
  healthy: number;
  warning: number;
  critical: number;
  unknown: number;
  pending: number;
}

const statusMap: Record<string, StatusTone> = {
  up: "healthy",
  warning: "warning",
  critical: "critical",
  unknown: "unknown",
  pending: "pending"
};

export function presentState(state: ServiceState): StatePresentation {
  const tone = statusMap[state.status] ?? "unknown";
  return {
    label: tone,
    tone,
    latency: state.latency_ms === null ? "—" : `${state.latency_ms} ms`,
    uptime: typeof state.uptime_pct === "number" ? `${state.uptime_pct.toFixed(1)}%` : "—",
    downtime: typeof state.downtime_pct === "number" ? `${state.downtime_pct.toFixed(1)}%` : "—",
    avgLatency: typeof state.avg_latency_ms === "number" ? `${state.avg_latency_ms} ms` : "—",
    downEvents: typeof state.down_events === "number" ? String(state.down_events) : "—"
  };
}

export function summarizeStates(states: ServiceState[]): StateSummary {
  const summary: StateSummary = {
    total: states.length,
    healthy: 0,
    warning: 0,
    critical: 0,
    unknown: 0,
    pending: 0
  };

  for (const state of states) {
    const tone = presentState(state).tone;
    summary[tone] += 1;
  }

  return summary;
}
