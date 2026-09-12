import { useEffect, useRef, useState } from "react";
import type { PointerEvent as ReactPointerEvent } from "react";
import type { ServiceState, StatusTone } from "./model";
import { presentState, summarizeStates } from "./model";
import { Logo } from "./Logo";

interface DashboardProps {
  states: ServiceState[];
  selectedName: string | null;
  onSelect: (name: string) => void;
}

interface HouseholdDevice {
  id: number;
  name: string;
  connector: string;
  endpoint: string | null;
  parent_id: number | null;
  metadata: Record<string, unknown>;
  status: string;
}

const summaryOrder: Array<Exclude<StatusTone, "unknown"> | "unknown"> = [
  "healthy",
  "warning",
  "critical",
  "unknown",
  "pending"
];

const CONSTELLATION_STORAGE_KEY = "raffael.constellation.positions";

function checkedLabel(value: string | null): string {
  if (!value) return "not yet";
  const date = new Date(value);
  if (Number.isNaN(date.valueOf())) return value;
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function constellationPosition(index: number, total: number): { x: number; y: number } {
  const columns = Math.max(3, Math.ceil(Math.sqrt(total * 1.8)));
  const column = index % columns;
  const row = Math.floor(index / columns);
  return {
    x: 14 + (column / Math.max(1, columns - 1)) * 72 + (row % 2 ? 5 : 0),
    y: 34 + (row % 3) * 25
  };
}

export function Dashboard({ states, selectedName, onSelect }: DashboardProps) {
  const summary = summarizeStates(states);
  const selected = states.find((state) => state.name === selectedName) ?? states[0] ?? null;
  const healthRate = summary.total === 0 ? null : Math.round((summary.healthy / summary.total) * 100);
  const [positions, setPositions] = useState<Record<string, { x: number; y: number }>>(() => {
    try {
      const stored = window.localStorage.getItem(CONSTELLATION_STORAGE_KEY);
      return stored ? JSON.parse(stored) as Record<string, { x: number; y: number }> : {};
    } catch {
      return {};
    }
  });
  const [dragging, setDragging] = useState<string | null>(null);
  const [hasUnsavedLayout, setHasUnsavedLayout] = useState(false);
  const [showAddClient, setShowAddClient] = useState(false);
  const [showDiscover, setShowDiscover] = useState(false);
  const [showSourceImport, setShowSourceImport] = useState(false);
  const [discoveryMessage, setDiscoveryMessage] = useState<string | null>(null);
  const [discovered, setDiscovered] = useState<Array<{ address: string; hostname: string | null; open_ports: number[] }>>([]);
  const [addClientMessage, setAddClientMessage] = useState<string | null>(null);
  const [sourceImportMessage, setSourceImportMessage] = useState<string | null>(null);
  const [devices, setDevices] = useState<HouseholdDevice[]>([]);
  const [clients, setClients] = useState<HouseholdDevice[]>([]);
  const draggedRef = useRef(false);

  useEffect(() => {
    if (!hasUnsavedLayout) return;
    const warnBeforeLeave = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = "";
    };
    window.addEventListener("beforeunload", warnBeforeLeave);
    return () => window.removeEventListener("beforeunload", warnBeforeLeave);
  }, [hasUnsavedLayout]);

  useEffect(() => {
    void refreshDevices();
  }, [showAddClient]);

  async function refreshDevices() {
    try {
      const [deviceResponse, clientResponse] = await Promise.all([
        fetch("/household/devices"),
        fetch("/household/clients"),
      ]);
      setDevices(deviceResponse.ok ? await deviceResponse.json() as HouseholdDevice[] : []);
      setClients(clientResponse.ok ? await clientResponse.json() as HouseholdDevice[] : []);
    } catch {
      setDevices([]);
      setClients([]);
    }
  }

  function positionFor(name: string, index: number): { x: number; y: number } {
    return positions[name] ?? constellationPosition(index, states.length);
  }

  function moveStar(event: ReactPointerEvent<HTMLButtonElement>, name: string) {
    if (!dragging || dragging !== name) return;
    const canvas = event.currentTarget.parentElement;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const x = Math.max(5, Math.min(95, ((event.clientX - rect.left) / rect.width) * 100));
    const y = Math.max(14, Math.min(86, ((event.clientY - rect.top) / rect.height) * 100));
    draggedRef.current = true;
    setPositions((current) => {
      const next = { ...current, [name]: { x, y } };
      window.localStorage.setItem(CONSTELLATION_STORAGE_KEY, JSON.stringify(next));
      return next;
    });
    setHasUnsavedLayout(true);
  }

  async function addClient(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const csrf = document.cookie.match(/(?:^|; )raffael_csrf=([^;]+)/)?.[1];
    const response = await fetch("/household/clients", {
      method: "POST",
      headers: { "Content-Type": "application/json", ...(csrf ? { "X-CSRF-Token": decodeURIComponent(csrf) } : {}) },
      body: JSON.stringify({
        connector: form.get("connector") || "icmp",
        name: form.get("name"),
        endpoint: form.get("endpoint") || null,
        mac_address: form.get("mac_address") || null,
        parent_id: form.get("parent_id") ? Number(form.get("parent_id")) : null,
      }),
    });
    if (!response.ok) {
      setAddClientMessage("could not add client");
      return;
    }
    setAddClientMessage("client added");
    const created = await response.json() as HouseholdDevice;
    setDevices((current) => [...current, created]);
    setClients((current) => [...current, created]);
    event.currentTarget.reset();
  }

  async function discover(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const csrf = document.cookie.match(/(?:^|; )raffael_csrf=([^;]+)/)?.[1];
    const response = await fetch("/household/discover", { method: "POST", headers: { "Content-Type": "application/json", ...(csrf ? { "X-CSRF-Token": decodeURIComponent(csrf) } : {}) }, body: JSON.stringify({ network: form.get("network"), workers: 32 }) });
    if (!response.ok) { setDiscoveryMessage("discovery failed"); return; }
    const results = await response.json() as Array<{ address: string; hostname: string | null; open_ports: number[] }>;
    setDiscovered(results);
    setDiscoveryMessage(`${results.length} devices found`);
  }

  async function adopt(item: { address: string; hostname: string | null; open_ports: number[] }) {
    const csrf = document.cookie.match(/(?:^|; )raffael_csrf=([^;]+)/)?.[1];
    const response = await fetch("/household/discover/adopt", { method: "POST", headers: { "Content-Type": "application/json", ...(csrf ? { "X-CSRF-Token": decodeURIComponent(csrf) } : {}) }, body: JSON.stringify(item) });
    if (!response.ok) { setDiscoveryMessage("could not add device"); return; }
    const created = await response.json() as HouseholdDevice;
    setDevices((current) => [...current, created]);
    setClients((current) => [...current, created]);
    setDiscovered((current) => current.filter((candidate) => candidate.address !== item.address));
    setDiscoveryMessage("device added");
  }

  async function importClientsFromSource(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSourceImportMessage("importing clients");
    const form = new FormData(event.currentTarget);
    const source = String(form.get("source") || "unifi");
    const parentId = form.get("parent_id");
    const params = new URLSearchParams();
    if (parentId) params.set("parent_id", String(parentId));
    const csrf = document.cookie.match(/(?:^|; )raffael_csrf=([^;]+)/)?.[1];
    const config = source === "unifi" ? {
      url: form.get("url") || undefined,
      site: form.get("site") || undefined,
      console_id: form.get("console_id") || undefined,
      username: form.get("username") || undefined,
      password: form.get("password") || undefined,
      api_key: form.get("api_key") || undefined,
    } : undefined;
    const response = await fetch(`/integrations/${source}/clients/import${params.size ? `?${params.toString()}` : ""}`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...(csrf ? { "X-CSRF-Token": decodeURIComponent(csrf) } : {}) },
      body: JSON.stringify(config || {}),
    });
    if (!response.ok) {
      const detail = await response.json().catch(() => null) as { detail?: string } | null;
      setSourceImportMessage(detail?.detail || "client import failed");
      return;
    }
    const result = await response.json() as { created: number; updated: number };
    await refreshDevices();
    setSourceImportMessage(`${result.created} added, ${result.updated} updated`);
  }

  function parentName(parentId: number | null): string {
    if (parentId === null) return "root";
    return devices.find((device) => device.id === parentId)?.name ?? `#${parentId}`;
  }

  return (
    <div className="shell">
      <aside className="rail" aria-label="Raffael navigation">
        <Logo />
        <div className="rail-line" />
        <div className="rail-item rail-item-active" aria-hidden="true">01</div>
        <div className="rail-spacer" />
        <div className="rail-version">0.4</div>
      </aside>

      <main className="workspace">
        <header className="topbar">
          <div>
            <Logo withName className="workspace-logo" />
            <p className="eyebrow">raffael / operations</p>
            <h1>system overview</h1>
          </div>
          <div className="topbar-actions">
            <button className="add-client-button" type="button" aria-label="discover network" onClick={() => setShowDiscover(true)}>⌁</button>
            <button className="add-client-button" type="button" aria-label="add client" onClick={() => setShowAddClient(true)}>+</button>
            <div className="live-indicator"><span /> monitoring</div>
            <a className="account-link" href="#/login">sign in</a>
          </div>
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

        <section className="widget-strip" aria-label="Monitoring overview">
          <article className="metric-widget metric-widget-wide">
            <div className="widget-label">monitoring posture</div>
            <div className="widget-value">{healthRate === null ? "—" : `${healthRate}%`}</div>
            <div className="widget-caption">healthy monitors</div>
            <div className="dot-meter" aria-hidden="true">
              {Array.from({ length: 20 }, (_, index) => <i className={healthRate !== null && index < Math.round(healthRate / 5) ? "is-on" : ""} key={index} />)}
            </div>
          </article>
          <article className="metric-widget">
            <div className="widget-label">attention</div>
            <div className={`widget-value ${summary.critical + summary.warning > 0 ? "is-alert" : ""}`}>{summary.critical + summary.warning}</div>
            <div className="widget-caption">warning or critical</div>
            <div className="signal-line" aria-hidden="true"><span /><span /><span /><span /><span /></div>
          </article>
          <article className="metric-widget">
            <div className="widget-label">last signal</div>
            <div className="widget-value widget-value-small">{selected ? presentState(selected).latency : "—"}</div>
            <div className="widget-caption">selected latency</div>
            <div className="widget-status-mark">{selected ? presentState(selected).label : "waiting"}</div>
          </article>
        </section>

        <div className="content-grid">
          <section className="overview-panel" aria-labelledby="overview-title">
            <div className="panel-heading">
              <div>
                <p className="section-kicker">current state</p>
                <h2 id="overview-title">client constellation</h2>
              </div>
              <div className="panel-heading-actions"><span className="panel-meta">{states.length} configured</span><button className="add-client-button" type="button" aria-label="add client" onClick={() => setShowAddClient(true)}>+</button></div>
            </div>
            <p className="topology-note">topology connections will appear once service dependencies are configured.</p>

            {states.length === 0 ? (
              <div className="empty-state">nothing configured yet.</div>
            ) : (
              <div className="star-grid">
                {states.map((state, index) => {
                  const view = presentState(state);
                  const selectedClass = selected?.name === state.name ? " is-selected" : "";
                  const position = positionFor(state.name, index);
                  return (
                    <button
                      className={`star tone-${view.tone}${selectedClass}${dragging === state.name ? " is-dragging" : ""}`}
                      key={state.name}
                      type="button"
                      style={{ left: `${position.x}%`, top: `${position.y}%` }}
                      onClick={() => { if (draggedRef.current) { draggedRef.current = false; return; } onSelect(state.name); }}
                      onPointerDown={(event) => { event.currentTarget.setPointerCapture(event.pointerId); setDragging(state.name); draggedRef.current = false; }}
                      onPointerMove={(event) => moveStar(event, state.name)}
                      onPointerUp={(event) => { event.currentTarget.releasePointerCapture(event.pointerId); setDragging(null); }}
                      onPointerCancel={() => setDragging(null)}
                      aria-label={`${state.name}: ${view.label}, ${view.latency}`}
                    >
                      <svg className="star-art" viewBox="0 0 100 100" aria-hidden="true">
                        <path d="M50 4v92M4 50h92M17.5 17.5l65 65M82.5 17.5l-65 65" />
                        <circle cx="50" cy="50" r="4" />
                      </svg>
                      <span className="star-inner">
                        <span className="star-name">{state.name}</span>
                        <span className="star-status"><span className="status-dot" />{view.label}</span>
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
                    <small>history is recording.</small>
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

        <section className="cluster-section" aria-labelledby="clusters-title">
          <div className="panel-heading">
            <div><p className="section-kicker">real service groups</p><h2 id="clusters-title">clusters</h2></div>
            <span className="panel-meta">derived from current status</span>
          </div>
          <div className="cluster-grid">
            {summaryOrder.map((tone) => {
              const members = states.filter((state) => presentState(state).tone === tone);
              return <article className={`cluster-card tone-${tone}`} key={tone}>
                <div className="cluster-title"><span className="status-dot" />{tone}<strong>{members.length}</strong></div>
                <div className="cluster-members">{members.length ? members.map((member) => <button type="button" key={member.name} onClick={() => onSelect(member.name)}>{member.name}</button>) : <span>none</span>}</div>
              </article>;
            })}
          </div>
        </section>

        <section className="clients-section" aria-labelledby="clients-title">
          <div className="panel-heading">
            <div><p className="section-kicker">network inventory</p><h2 id="clients-title">clients</h2></div>
            <div className="panel-heading-actions">
              <span className="panel-meta">{clients.length} saved</span>
              <button className="source-import-button" type="button" onClick={() => setShowSourceImport(true)}>import source</button>
              <button className="add-client-button" type="button" aria-label="add client" onClick={() => setShowAddClient(true)}>+</button>
            </div>
          </div>
          {clients.length === 0 ? (
            <div className="clients-empty">no clients saved yet.</div>
          ) : (
            <div className="clients-table" role="table" aria-label="Saved clients">
              <div className="clients-row clients-row-head" role="row">
                <span role="columnheader">name</span>
                <span role="columnheader">endpoint</span>
                <span role="columnheader">parent</span>
                <span role="columnheader">connector</span>
                <span role="columnheader">mac</span>
              </div>
              {clients.map((client) => (
                <div className="clients-row" role="row" key={client.id}>
                  <strong role="cell">{client.name}</strong>
                  <span role="cell">{client.endpoint || "not set"}</span>
                  <span role="cell">{parentName(client.parent_id)}</span>
                  <span role="cell">{client.connector}</span>
                  <span role="cell">{String(client.metadata.mac_address || "not set")}</span>
                </div>
              ))}
            </div>
          )}
        </section>

        <footer className="workspace-footnote">raffael · local infrastructure · v0.6</footer>

        {showAddClient ? (
          <div className="client-dialog-backdrop" role="presentation" onClick={() => setShowAddClient(false)}>
            <section className="client-dialog" role="dialog" aria-modal="true" aria-labelledby="add-client-title" onClick={(event) => event.stopPropagation()}>
              <button className="client-dialog-close" type="button" aria-label="close" onClick={() => setShowAddClient(false)}>×</button>
              <p className="section-kicker">raffael / clients</p>
              <h2 id="add-client-title">new client</h2>
              <form className="client-dialog-form" onSubmit={addClient}>
                <label><span className="sr-only">name</span><input name="name" aria-label="name" placeholder="name" autoFocus required /></label>
                <label><span className="sr-only">endpoint</span><input name="endpoint" aria-label="ip or hostname" placeholder="ip or hostname" /></label>
                <label><span className="sr-only">mac address</span><input name="mac_address" aria-label="mac address" placeholder="mac address (optional)" /></label>
                <label><span className="sr-only">connector</span><select name="connector" aria-label="connector" defaultValue="icmp"><option value="icmp">ping / network</option><option value="generic">generic service</option><option value="snmp">SNMP</option><option value="unifi">unifi</option><option value="hue">philips hue</option><option value="proxmox">proxmox</option><option value="docker">docker</option><option value="ssh">SSH Linux</option><option value="windows-agent">windows</option><option value="macos-agent">macos</option></select></label>
                <label><span className="sr-only">parent device</span><select name="parent_id" aria-label="parent device" defaultValue=""><option value="">no parent (root device)</option>{devices.map((device) => <option key={device.id} value={device.id}>{device.name} · {device.connector}</option>)}</select></label>
                <button className="client-dialog-submit" type="submit"><span>+</span> add client</button>
                {addClientMessage ? <p className="client-dialog-message" role="status">{addClientMessage}</p> : null}
              </form>
            </section>
          </div>
        ) : null}
        {showDiscover ? (
          <div className="client-dialog-backdrop" role="presentation" onClick={() => setShowDiscover(false)}>
            <section className="client-dialog" role="dialog" aria-modal="true" aria-labelledby="discover-title" onClick={(event) => event.stopPropagation()}>
              <button className="client-dialog-close" type="button" aria-label="close" onClick={() => setShowDiscover(false)}>×</button>
              <p className="section-kicker">raffael / discovery</p><h2 id="discover-title">scan network</h2>
              <form className="client-dialog-form" onSubmit={discover}><label><span className="sr-only">network</span><input name="network" aria-label="network" defaultValue="192.168.1.0/24" required /></label><button className="client-dialog-submit" type="submit">scan</button></form>
              {discoveryMessage ? <p className="client-dialog-message" role="status">{discoveryMessage}</p> : null}
              {discovered.length ? <div className="cluster-members">{discovered.map((item) => <span key={item.address}>{item.hostname || item.address}{item.open_ports.length ? ` · ${item.open_ports.join(", ")}` : ""}<button type="button" onClick={() => adopt(item)} aria-label={`add ${item.address}`}>+</button></span>)}</div> : null}
            </section>
          </div>
        ) : null}
        {showSourceImport ? (
          <div className="client-dialog-backdrop" role="presentation" onClick={() => setShowSourceImport(false)}>
            <section className="client-dialog" role="dialog" aria-modal="true" aria-labelledby="source-import-title" onClick={(event) => event.stopPropagation()}>
              <button className="client-dialog-close" type="button" aria-label="close" onClick={() => setShowSourceImport(false)}>×</button>
              <p className="section-kicker">raffael / sources</p>
              <h2 id="source-import-title">import clients</h2>
              <form className="client-dialog-form" onSubmit={importClientsFromSource}>
                <label><span className="sr-only">source</span><select name="source" aria-label="source" defaultValue="unifi"><option value="unifi">unifi network</option><option value="api">generic api</option><option value="snmp">snmp targets</option></select></label>
                <label><span className="sr-only">UniFi URL</span><input name="url" aria-label="UniFi URL" placeholder="https://192.168.1.1" /></label>
                <label><span className="sr-only">UniFi site</span><input name="site" aria-label="UniFi site" placeholder="default" defaultValue="default" /></label>
                <label><span className="sr-only">UniFi API key</span><input name="api_key" aria-label="UniFi API key" type="password" placeholder="API key (optional)" /></label>
                <p className="client-dialog-message">Raffael erkennt lokale UniFi-API und Site automatisch.</p>
                <label><span className="sr-only">UniFi username</span><input name="username" aria-label="UniFi username" placeholder="username (optional)" /></label>
                <label><span className="sr-only">UniFi password</span><input name="password" aria-label="UniFi password" type="password" placeholder="password (optional)" /></label>
                <label><span className="sr-only">parent device</span><select name="parent_id" aria-label="parent device" defaultValue=""><option value="">no parent (root clients)</option>{devices.map((device) => <option key={device.id} value={device.id}>{device.name} · {device.connector}</option>)}</select></label>
                <button className="client-dialog-submit" type="submit"><span>in</span> import clients</button>
                {sourceImportMessage ? <p className="client-dialog-message" role="status">{sourceImportMessage}</p> : null}
              </form>
            </section>
          </div>
        ) : null}
      </main>
    </div>
  );
}
