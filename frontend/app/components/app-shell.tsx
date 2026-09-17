import { useEffect, useState, type CSSProperties } from "react";
import { API_URL, type View } from "../simulation";

export function AppHeader({
  view,
  onNavigate,
  hasResults,
  loading,
}: {
  view: View;
  onNavigate: (view: View) => void;
  hasResults: boolean;
  loading: boolean;
}) {
  const [status, setStatus] = useState<"checking" | "online" | "offline">("checking");
  useEffect(() => {
    let active = true;
    let controller: AbortController | undefined;
    async function checkHealth() {
      controller?.abort();
      controller = new AbortController();
      const timeout = window.setTimeout(() => controller?.abort(), 5000);
      try {
        const response = await fetch(`${API_URL}/health`, { signal: controller.signal, cache: "no-store" });
        const data = await response.json();
        if (active) setStatus(response.ok && data.status === "healthy" ? "online" : "offline");
      } catch {
        if (active) setStatus("offline");
      } finally {
        window.clearTimeout(timeout);
      }
    }
    void checkHealth();
    const interval = window.setInterval(checkHealth, 30000);
    return () => {
      active = false;
      controller?.abort();
      window.clearInterval(interval);
    };
  }, []);
  const views = ["simulation", "experiments", "results"] as const;
  return (
    <header className="app-header">
      <div className="brand-row">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">
            M<span>/</span>S
          </span>
          <div>
            <h1>MarketSim</h1>
            <p>Market Making Simulation &amp; Strategy Laboratory</p>
          </div>
        </div>
        <div className={`api-status ${status}`} role="status">
          <span />
          {status === "checking" ? "Checking API" : status === "online" ? "API Online" : "API Offline"}
        </div>
      </div>
      <div className="navigation-row">
        <nav
          className="app-navigation"
          aria-label="Application views"
          style={{ "--active-tab": views.indexOf(view) } as CSSProperties}
        >
          <span className="navigation-indicator" aria-hidden="true" />
          {views.map((item) => (
            <button
              type="button"
              key={item}
              aria-current={view === item ? "page" : undefined}
              onClick={() => onNavigate(item)}
              disabled={loading}
            >
              <span>
                {item === "simulation" ? "Simulation" : item === "results" ? "Results" : "Experiments"}
              </span>
              {item === "results" && hasResults && <i className="result-dot" aria-hidden="true" />}
            </button>
          ))}
        </nav>
        <span className="environment-label">
          LIMIT ORDER BOOK <span>/</span> SIMULATION
        </span>
      </div>
    </header>
  );
}

export function LoadingState({ label }: { label: string }) {
  return (
    <div className="loading-state" role="status" aria-live="polite">
      <span className="spinner" />
      <div>
        <strong>{label} is running</strong>
        <p>Processing the market path and strategy results. Larger experiments may take a little longer.</p>
      </div>
      <div className="loading-track" aria-hidden="true">
        <span />
      </div>
    </div>
  );
}
