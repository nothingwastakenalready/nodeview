import { useEffect, useState } from "react";

import { Dashboard } from "./Dashboard";
import { LoginPage } from "./LoginPage";
import type { ServiceState } from "./model";

const refreshMs = 5000;

export function App() {
  const [route, setRoute] = useState(window.location.hash || "#/dashboard");
  const [authenticated, setAuthenticated] = useState<boolean | null>(null);
  const [states, setStates] = useState<ServiceState[]>([]);
  const [selectedName, setSelectedName] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/auth/me", { headers: { Accept: "application/json" } })
      .then((response) => setAuthenticated(response.ok))
      .catch(() => setAuthenticated(false));
  }, []);

  useEffect(() => {
    const onHashChange = () => setRoute(window.location.hash || "#/dashboard");
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  useEffect(() => {
    let active = true;

    async function loadState() {
      try {
        const response = await fetch("/state", { headers: { Accept: "application/json" } });
        if (!response.ok) throw new Error(`state request failed (${response.status})`);
        const data = await response.json() as ServiceState[];
        if (!active) return;
        setStates(data);
        setSelectedName((current) => {
          if (current && data.some((state) => state.name === current)) return current;
          return data[0]?.name ?? null;
        });
        setError(null);
      } catch (reason) {
        if (!active) return;
        setError(reason instanceof Error ? reason.message : "could not load state");
      } finally {
        if (active) setLoading(false);
      }
    }

    void loadState();
    const timer = window.setInterval(() => void loadState(), refreshMs);

    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, []);

  if (route === "#/login" || route === "#/register" || authenticated === false) {
    return <LoginPage register={route === "#/register"} onAuthenticated={() => { setAuthenticated(true); window.location.hash = "#/dashboard"; }} />;
  }

  if (authenticated === null) return <div className="boot-state">checking session.</div>;

  if (loading) {
    return <div className="boot-state">raffael is looking around.</div>;
  }

  if (error && states.length === 0) {
    return (
      <div className="boot-state boot-error">
        <strong>state unavailable</strong>
        <span>{error}</span>
      </div>
    );
  }

  return (
    <>
      {error ? <div className="stale-banner">refresh failed. showing the last state we have.</div> : null}
      <Dashboard states={states} selectedName={selectedName} onSelect={setSelectedName} />
    </>
  );
}
