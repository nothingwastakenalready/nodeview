export type EngineStatus = "up" | "warning" | "critical" | "unknown" | "pending" | string;

export interface ServiceState {
  name: string;
  status: EngineStatus;
  latency_ms: number | null;
  http_status: number | null;
  error: string | null;
  last_checked: string | null;
  consecutive_successes: number;
  consecutive_failures: number;
}

export type StatusTone = "healthy" | "warning" | "critical" | "unknown" | "pending";

export interface StatePresentation {
  label: StatusTone;
  tone: StatusTone;
  latency: string;
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
    latency: state.latency_ms === null ? "—" : `${state.latency_ms} ms`
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
