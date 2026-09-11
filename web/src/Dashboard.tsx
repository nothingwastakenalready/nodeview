import type { ServiceState, StatusTone } from "./model";
import { presentState, summarizeStates } from "./model";

interface DashboardProps {
  states: ServiceState[];
  selectedName: string | null;
  onSelect: (name: string) => void;
}

const summaryOrder: Array<Exclude<StatusTone, "unknown"> | "unknown"> = [
  "healthy",
  "warning",
  "critical",
  "unknown",
  "pending"
];

function checkedLabel(value: string | null): string {
  if (!value) return "not yet";
  const date = new Date(value);
  if (Number.isNaN(date.valueOf())) return value;
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

export function Dashboard({ states, selectedName, onSelect }: DashboardProps) {
  const summary = summarizeStates(states);
  const selected = states.find((state) => state.name === selectedName) ?? states[0] ?? null;

  return (
    <div className="shell">
      <aside className="rail" aria-label="NodeView navigation">
        <div className="brand-mark" aria-label="NodeView">nv</div>
        <div className="rail-line" />
        <div className="rail-item rail-item-active" aria-hidden="true">01</div>
        <div className="rail-spacer" />
        <div className="rail-version">0.3</div>
      </aside>

      <main className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">nodeview / live</p>
            <h1>infrastructure</h1>
          </div>
          <div className="live-indicator"><span /> monitoring</div>
        </header>

        <section className="summary" aria-label="Current status summary">
          <div className="summary-total">
            <strong>{summary.total}</strong>
            <span>monitors</span>
          </div>
          {summaryOrder.map((tone) => (
            <div className={`summary-item tone-${tone}`} key={tone}>
              <span className="status-dot" />
              <span>{tone}</span>
              <strong>{summary[tone]}</strong>
            </div>
          ))}
        </section>

        <div className="content-grid">
          <section className="overview-panel" aria-labelledby="overview-title">
            <div className="panel-heading">
              <div>
                <p className="section-kicker">current state</p>
                <h2 id="overview-title">overview</h2>
              </div>
              <span className="panel-meta">{states.length} configured</span>
            </div>

            {states.length === 0 ? (
              <div className="empty-state">nothing configured yet.</div>
            ) : (
              <div className="hex-grid">
                {states.map((state) => {
                  const view = presentState(state);
                  const selectedClass = selected?.name === state.name ? " is-selected" : "";
                  return (
                    <button
                      className={`hex tone-${view.tone}${selectedClass}`}
                      key={state.name}
                      type="button"
                      onClick={() => onSelect(state.name)}
                      aria-label={`${state.name}: ${view.label}, ${view.latency}`}
                    >
                      <span className="hex-inner">
                        <span className="hex-name">{state.name}</span>
                        <strong className="hex-latency">{view.latency}</strong>
                        <span className="hex-status"><span className="status-dot" />{view.label}</span>
                      </span>
                    </button>
                  );
                })}
              </div>
            )}
          </section>

          <aside className="detail-panel" aria-live="polite">
            {selected ? (() => {
              const view = presentState(selected);
              return (
                <>
                  <div className="detail-head">
                    <div>
                      <p className="section-kicker">selected monitor</p>
                      <h2>{selected.name}</h2>
                    </div>
                    <span className={`status-pill tone-${view.tone}`}><span className="status-dot" />{view.label}</span>
                  </div>

                  <div className="latency-block">
                    <span>latency now</span>
                    <strong>{view.latency}</strong>
                    <small>history lands with persistence.</small>
                  </div>

                  <dl className="detail-list">
                    <div>
                      <dt>last checked</dt>
                      <dd>{checkedLabel(selected.last_checked)}</dd>
                    </div>
                    <div>
                      <dt>response</dt>
                      <dd>{selected.http_status === null ? "not http" : `http ${selected.http_status}`}</dd>
                    </div>
                    <div>
                      <dt>success streak</dt>
                      <dd>{selected.consecutive_successes}</dd>
                    </div>
                    <div>
                      <dt>failure streak</dt>
                      <dd>{selected.consecutive_failures}</dd>
                    </div>
                  </dl>

                  <div className="detail-error">
                    <span>last error</span>
                    <p>{selected.error ?? "none"}</p>
                  </div>
                </>
              );
            })() : (
              <div className="empty-state">select something once it exists.</div>
            )}
          </aside>
        </div>
      </main>
    </div>
  );
}
