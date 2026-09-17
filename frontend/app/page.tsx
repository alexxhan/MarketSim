"use client";

import { useEffect, useRef, useState } from "react";
import { AppHeader, LoadingState } from "./components/app-shell";
import { ConfigurationPanel, SimulationTypeSelector } from "./components/configuration-panel";
import { EmptyResults, ResultsWorkspace } from "./components/results-workspace";
import {
  initialConfiguration,
  isExperiment,
  modes,
  runSimulation,
  type Mode,
  type RunResult,
  type View,
} from "./simulation";

export default function Home() {
  const [view, setView] = useState<View>("simulation");
  const [simulationMode, setSimulationMode] = useState<Mode>("single");
  const [experimentMode, setExperimentMode] = useState<Mode>("experiment");
  const [configuration, setConfiguration] = useState(initialConfiguration);
  const [result, setResult] = useState<RunResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pending = useRef(false);
  const workspace = useRef<HTMLElement>(null);
  const mode = view === "experiments" ? experimentMode : simulationMode;

  useEffect(() => {
    workspace.current?.focus({ preventScroll: true });
  }, [view]);

  function navigate(nextView: View) {
    setView(nextView);
    window.scrollTo({ top: 0, behavior: "instant" });
  }

  function selectMode(nextMode: Mode) {
    if (isExperiment(nextMode)) setExperimentMode(nextMode);
    else setSimulationMode(nextMode);
    setError(null);
    navigate(isExperiment(nextMode) ? "experiments" : "simulation");
  }

  async function run() {
    if (pending.current) return;
    pending.current = true;
    setLoading(true);
    setError(null);
    try {
      const nextResult = await runSimulation(mode, { ...configuration });
      setResult(nextResult);
      navigate("results");
    } catch (error) {
      setError(error instanceof Error ? error.message : "Unable to complete the run. Please try again.");
    } finally {
      pending.current = false;
      setLoading(false);
    }
  }

  return (
    <div className="app-shell">
      <a className="skip-link" href="#workspace">
        Skip to workspace
      </a>
      <AppHeader view={view} onNavigate={navigate} hasResults={!!result} loading={loading} />
      <main id="workspace" ref={workspace} tabIndex={-1} className="workspace" aria-busy={loading}>
        <div key={view} className="view-transition">
          {view === "results" ? (
            result ? (
              <ResultsWorkspace result={result} onAdjust={() => selectMode(result.mode)} />
            ) : (
              <EmptyResults onConfigure={() => navigate("simulation")} />
            )
          ) : (
            <>
              <div className="workspace-heading configuration-intro">
                <div>
                  <p className="eyebrow">{view === "experiments" ? "Experiments" : "Simulation"}</p>
                  <h2>{view === "experiments" ? "Test the assumptions." : "Define your market."}</h2>
                  <p>
                    {view === "experiments"
                      ? "Explore sensitivity, seed variation, and changing market regimes."
                      : "Configure a seeded market-making simulation."}
                  </p>
                </div>
              </div>
              <div className="configuration-layout">
                <SimulationTypeSelector mode={mode} onChange={selectMode} disabled={loading} />
                <div className="configuration-content">
                  {loading && <LoadingState label={modes.find((item) => item.id === mode)!.label} />}
                  <ConfigurationPanel
                    mode={mode}
                    config={configuration}
                    onChange={setConfiguration}
                    onRun={() => void run()}
                    loading={loading}
                    error={error}
                  />
                </div>
              </div>
            </>
          )}
        </div>
      </main>
      <footer className="app-footer">
        <span>
          MarketSim <span>/</span> Strategy Laboratory
        </span>
        <p>Educational simulation. Synthetic order flow. No real trades.</p>
      </footer>
    </div>
  );
}
