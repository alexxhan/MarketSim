"use client";

import { useState } from "react";
import { scenarioPresets, type Regime } from "./scenarios";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ReferenceLine,
  ResponsiveContainer,
} from "recharts";

type SimulationResults = {
  ticks: number;
  total_trades: number;
  total_market_trades: number;
  market_maker_fills: number;
  market_maker_buy_fills: number;
  market_maker_sell_fills: number;
  market_maker_executed_volume: number;
  average_absolute_inventory: number;
  maximum_absolute_inventory: number;
  pnl_per_fill: number | null;
  final_cash: number;
  final_inventory: number;
  final_portfolio_value: number | null;
  final_pnl: number | null;
  final_midprice: number | null;
};

type SimulationHistory = {
  pnl: (number | null)[];
  inventory: number[];
  midprice: (number | null)[];
};

type SimulationResponse = {
  results: SimulationResults;
  history: SimulationHistory;
};

type Comparison = {
  basic: SimulationResponse;
  inventory: SimulationResponse;
  seed: number;
};

type ExperimentAggregate = {
  valid_pnl_count: number;
  unavailable_pnl_count: number;
  average_pnl: number | null;
  pnl_standard_deviation: number | null;
  best_pnl: number | null;
  worst_pnl: number | null;
  average_final_inventory: number;
  average_absolute_inventory: number;
  average_maximum_absolute_inventory: number;
  worst_maximum_absolute_inventory: number;
  average_market_maker_fills: number;
  average_market_maker_executed_volume: number;
};

type ExperimentSeedResult = {
  final_pnl: number | null;
  maximum_absolute_inventory: number;
};

type ExperimentResponse = {
  config: { number_of_simulations: number; starting_seed: number; ticks: number };
  per_seed: { seed: number; basic: ExperimentSeedResult; inventory: ExperimentSeedResult }[];
  aggregates: { basic: ExperimentAggregate; inventory: ExperimentAggregate };
};

type ScenarioResponse = {
  config: { regimes: Regime[]; seed: number; strategy: string };
  total_ticks: number;
  regime_boundaries: { regime_id: number; name: string; start_tick: number; end_tick: number }[];
  runs: Partial<Record<"basic" | "inventory", {
    results: SimulationResults;
    history: SimulationHistory & { regime_id: number[]; regime_name: string[] };
  }>>;
};

function ScenarioResults({ scenario }: { scenario: ScenarioResponse }) {
  const strategies = (["basic", "inventory"] as const).filter((key) => scenario.runs[key]);
  return (
    <section className="space-y-6">
      <h2 className="text-2xl font-semibold">Scenario Stress Test Results</h2>
      <p className="text-sm text-gray-500">{scenario.total_ticks} ticks · Seed: {scenario.config.seed}. Market price is each strategy’s order-book midprice.</p>
      <p>{scenario.regime_boundaries.map((regime) => `${regime.name} (ticks ${regime.start_tick}–${regime.end_tick})`).join(" | ")}</p>
      <div className="grid gap-6 md:grid-cols-2">
        {strategies.map((key) => (
          <div key={key} className="space-y-5 rounded-2xl border border-white/10 bg-[#0e1219] p-5 text-gray-100">
            <h3 className={`text-lg font-semibold ${key === "basic" ? "text-blue-400" : "text-amber-400"}`}>{key === "basic" ? "Basic Market Maker" : "Inventory-Aware Market Maker"}</h3>
            <SimulationMetrics results={scenario.runs[key]!.results} />
          </div>
        ))}
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        {([
          ["pnl", "P&L Through Scenario"],
          ["inventory", "Inventory Through Scenario"],
          ["midprice", "Market Price Through Scenario"],
        ] as const).map(([metric, title]) => (
          <div key={metric} className={metric === "midprice" ? "lg:col-span-2" : ""}>
            <h3 className="mb-3 text-lg font-medium">{title}</h3>
            <div className="h-80 rounded-2xl border border-white/10 bg-[#0e1219] p-4">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart margin={{ top: 25, right: 20 }} data={Array.from({ length: scenario.total_ticks }, (_, index) => ({
                  tick: index + 1,
                  basic: scenario.runs.basic?.history[metric][index],
                  inventory: scenario.runs.inventory?.history[metric][index],
                }))}>
                  <XAxis dataKey="tick" type="number" domain={[1, scenario.total_ticks]} tickLine={false} />
                  <YAxis domain={["auto", "auto"]} tickLine={false} />
                  <Tooltip labelFormatter={(tick) => {
                    const regime = scenario.regime_boundaries.find((item) => Number(tick) >= item.start_tick && Number(tick) <= item.end_tick);
                    return `Tick ${tick} · ${regime?.name ?? ""}`;
                  }} />
                  <Legend />
                  {scenario.regime_boundaries.slice(1).map((regime) => (
                    <ReferenceLine key={regime.regime_id} x={regime.start_tick} stroke="#9ca3af" strokeDasharray="4 4" label={{ value: `${regime.name} (${regime.start_tick})`, position: "top", fill: "#9ca3af", fontSize: 11 }} />
                  ))}
                  {strategies.map((key) => (
                    <Line key={key} type="linear" dataKey={key} name={key === "basic" ? "Basic" : "Inventory-Aware"} stroke={key === "basic" ? "#60a5fa" : "#fbbf24"} strokeDasharray={key === "basic" ? undefined : "6 3"} dot={false} strokeWidth={2} connectNulls={false} />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

const sweepParameters = {
  volatility: { label: "Volatility", defaults: "1, 2, 3, 4, 5" },
  buy_pressure: { label: "Buy Pressure", defaults: "0.40, 0.45, 0.50, 0.55, 0.60" },
  order_arrival_rate: { label: "Market Activity", defaults: "1, 2, 3, 4, 5" },
  spread: { label: "Spread", defaults: "0.02, 0.04, 0.06, 0.08, 0.10" },
  inventory_risk_factor: { label: "Inventory Risk Factor", defaults: "0.000, 0.001, 0.002, 0.003, 0.005" },
};

type SweepParameter = keyof typeof sweepParameters;
type SweepResponse = {
  config: { simulations_per_value: number; starting_seed: number; ticks: number };
  sweep_parameter: SweepParameter;
  results: { value: number; basic: ExperimentAggregate; inventory: ExperimentAggregate }[];
};

function sweepValueLabel(parameter: SweepParameter, value: number) {
  return parameter === "buy_pressure" ? `${Number((value * 100).toFixed(6))}%` : String(value);
}

const sweepMetrics = [
  ["average_pnl", "Average P&L", true],
  ["pnl_standard_deviation", "P&L Std Dev", true],
  ["best_pnl", "Best P&L", true],
  ["worst_pnl", "Worst P&L", true],
  ["average_absolute_inventory", "Average |Inventory|", false],
  ["average_maximum_absolute_inventory", "Average Max |Inventory|", false],
  ["worst_maximum_absolute_inventory", "Worst Max |Inventory|", false],
  ["average_market_maker_fills", "Average MM Fills", false],
  ["average_market_maker_executed_volume", "Average Executed Volume", false],
] as const;

function SweepResults({ sweep }: { sweep: SweepResponse }) {
  const parameter = sweep.sweep_parameter;
  const label = sweepParameters[parameter].label;
  const chartPoints = [...sweep.results].sort((a, b) => a.value - b.value);
  return (
    <section className="space-y-6">
      <h2 className="text-2xl font-semibold">Parameter Sweep Results: {label}</h2>
      <p className="text-sm text-gray-500">
        {sweep.config.simulations_per_value} seed pairs per value, {sweep.config.ticks} ticks each.
        Every value uses seeds {sweep.config.starting_seed} through {sweep.config.starting_seed + sweep.config.simulations_per_value - 1}.
        P&amp;L statistics exclude unavailable values and use population standard deviation. Chart gaps indicate unavailable P&amp;L.
      </p>
      {parameter === "inventory_risk_factor" && <p className="text-sm text-gray-500">Basic is an unchanged baseline at every risk factor. Only Inventory-Aware is affected.</p>}
      <div className="overflow-x-auto rounded-2xl border border-white/10 bg-[#0e1219] p-4 text-gray-100">
        <table className="w-full text-left text-sm">
          <caption className="mb-3 text-left text-gray-400">Each cell shows Basic (blue) followed by Inventory-Aware (amber).</caption>
          <thead>
            <tr>
              <th scope="col" className="p-3">{label}</th>
              {sweepMetrics.map(([key, title]) => <th key={key} scope="col" className="min-w-32 p-3">{title}</th>)}
              <th scope="col" className="min-w-32 p-3">P&amp;L Available / Missing</th>
            </tr>
          </thead>
          <tbody>
            {sweep.results.map((point, index) => (
              <tr key={index} className="border-t border-gray-700">
                <th scope="row" className="whitespace-nowrap p-3">{sweepValueLabel(parameter, point.value)}</th>
                {sweepMetrics.map(([key, , money]) => (
                  <td key={key} className="p-3">
                    {(["basic", "inventory"] as const).map((strategy) => {
                      const value = point[strategy][key];
                      return <div key={strategy} className={strategy === "basic" ? "text-blue-400" : "text-amber-400"}>
                        <span className="sr-only">{strategy === "basic" ? "Basic: " : "Inventory-Aware: "}</span>
                        {money ? currency(value) : value === null ? "Unavailable" : value.toFixed(2)}
                      </div>;
                    })}
                  </td>
                ))}
                <td className="p-3">
                  <div className="text-blue-400">{point.basic.valid_pnl_count} / {point.basic.unavailable_pnl_count}</div>
                  <div className="text-amber-400">{point.inventory.valid_pnl_count} / {point.inventory.unavailable_pnl_count}</div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        {([
          ["average_pnl", "Average P&L"],
          ["pnl_standard_deviation", "P&L Standard Deviation"],
          ["average_absolute_inventory", "Average Absolute Inventory"],
          ["average_market_maker_fills", "Average Market Maker Fills"],
        ] as const).map(([metric, title]) => (
          <div key={metric}>
            <h3 className="mb-3 text-lg font-medium">{title} vs {label}</h3>
            <div className="h-80 rounded-2xl border border-white/10 bg-[#0e1219] p-4">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartPoints.map((point) => ({ value: point.value, basic: point.basic[metric], inventory: point.inventory[metric] }))}>
                  <XAxis dataKey="value" type="number" domain={["dataMin", "dataMax"]} tickLine={false} tickFormatter={(value: number) => sweepValueLabel(parameter, value)} />
                  <YAxis domain={["auto", "auto"]} tickLine={false} />
                  <Tooltip labelFormatter={(value) => `${label}: ${sweepValueLabel(parameter, Number(value))}`} />
                  <Legend />
                  <Line type="linear" dataKey="basic" name="Basic" stroke="#60a5fa" dot={{ r: 3 }} strokeWidth={2} connectNulls={false} />
                  <Line type="linear" dataKey="inventory" name="Inventory-Aware" stroke="#fbbf24" dot={{ r: 3 }} strokeDasharray="6 3" strokeWidth={2} connectNulls={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function currency(value: number | null) {
  return value === null ? "Unavailable" : `$${value.toFixed(2)}`;
}

function SimulationMetrics({ results }: { results: SimulationResults }) {
  return (
    <div className="space-y-5">
      <section className="space-y-2">
        <h4 className="text-sm font-semibold uppercase text-gray-400">Performance</h4>
        <p>Final P&amp;L: {currency(results.final_pnl)}</p>
        <p>Final Portfolio Value: {currency(results.final_portfolio_value)}</p>
        <p>Cash: {currency(results.final_cash)}</p>
        <p>P&amp;L per Fill: {currency(results.pnl_per_fill)}</p>
        <p>Midprice: {currency(results.final_midprice)}</p>
      </section>
      <section className="space-y-2">
        <h4 className="text-sm font-semibold uppercase text-gray-400">Execution</h4>
        <p>Total Market Trades: {results.total_market_trades}</p>
        <p>Market Maker Fills: {results.market_maker_fills}</p>
        <p>Market Maker Buy Fills: {results.market_maker_buy_fills}</p>
        <p>Market Maker Sell Fills: {results.market_maker_sell_fills}</p>
        <p>Market Maker Executed Volume: {results.market_maker_executed_volume}</p>
      </section>
      <section className="space-y-2">
        <h4 className="text-sm font-semibold uppercase text-gray-400">Inventory Risk</h4>
        <p>Final Inventory: {results.final_inventory}</p>
        <p>Average Absolute Inventory: {results.average_absolute_inventory.toFixed(2)}</p>
        <p>Maximum Absolute Inventory: {results.maximum_absolute_inventory}</p>
      </section>
    </div>
  );
}

export default function Home() {
  const [mode, setMode] = useState("single");
  const [scenarioIndex, setScenarioIndex] = useState(0);
  const [scenarioStrategy, setScenarioStrategy] = useState("comparison");
  const [scenario, setScenario] = useState<ScenarioResponse | null>(null);
  const [strategy, setStrategy] = useState("inventory");
  const [startingPrice, setStartingPrice] = useState(100);
  const [seed, setSeed] = useState(42);
  const [startingSeed, setStartingSeed] = useState(42);
  const [numberOfSimulations, setNumberOfSimulations] = useState(10);
  const [experiment, setExperiment] = useState<ExperimentResponse | null>(null);
  const [sweep, setSweep] = useState<SweepResponse | null>(null);
  const [sweepParameter, setSweepParameter] = useState<SweepParameter>("volatility");
  const [sweepValues, setSweepValues] = useState<string>(sweepParameters.volatility.defaults);
  const [simulationsPerValue, setSimulationsPerValue] = useState(10);
  const [ticks, setTicks] = useState(1000);
  const [volatility, setVolatility] = useState(3);
  const [buyPressure, setBuyPressure] = useState(0.5);
  const [orderArrivalRate, setOrderArrivalRate] = useState(3);
  const [spread, setSpread] = useState(0.04);
  const [orderSize, setOrderSize] = useState(10);
  const [riskFactor, setRiskFactor] = useState(0.001);

  const [results, setResults] = useState<SimulationResults | null>(null);
  const [history, setHistory] = useState<SimulationHistory | null>(null);
  const [loading, setLoading] = useState(false);
  const [comparison, setComparison] = useState<Comparison | null>(null);
  const [error, setError] = useState<string | null>(null);

  const sweepTokens = sweepValues.split(",").map((value) => value.trim());
  const parsedSweepValues = sweepTokens.map(Number);
  const validSweepValues = sweepTokens.length <= 10 && sweepTokens.every((value) => value !== "") && parsedSweepValues.every((value) => {
    if (!Number.isFinite(value)) return false;
    if (sweepParameter === "volatility") return Number.isInteger(value) && value >= 0 && value <= 20;
    if (sweepParameter === "order_arrival_rate") return Number.isInteger(value) && value >= 1 && value <= 10;
    if (sweepParameter === "buy_pressure") return value >= 0 && value <= 1;
    if (sweepParameter === "spread") return value > 0;
    return value >= 0;
  });
  const sweepWorkload = 2 * simulationsPerValue * ticks * parsedSweepValues.reduce((sum, value) => sum + (sweepParameter === "order_arrival_rate" ? value : orderArrivalRate), 0);
  const sweepError = !validSweepValues
    ? "Enter 1–10 comma-separated values: volatility integers 0–20; activity integers 1–10; buy pressure 0–1; spread > 0; risk factor >= 0."
    : sweepWorkload > 1000000 ? "Reduce sweep values, simulations, ticks, or market activity to stay within 1,000,000 external orders." : null;

  async function runSimulation() {
    setLoading(true);
    setError(null);
    setResults(null);
    setHistory(null);
    setComparison(null);
    setExperiment(null);
    setSweep(null);
    setScenario(null);

    try {
      const sharedConfig = {
        ticks,
        starting_price: startingPrice,
        volatility,
        buy_pressure: buyPressure,
        order_arrival_rate: orderArrivalRate,
        spread,
        order_size: orderSize,
        seed,
      };

      async function runStrategy(selectedStrategy: string): Promise<SimulationResponse> {
        const response = await fetch(
          "http://localhost:8000/simulation/run",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              ...sharedConfig,
              strategy: selectedStrategy,
              ...(selectedStrategy === "inventory"
                ? { inventory_risk_factor: riskFactor }
                : {}),
            }),
          }
        );

        if (!response.ok) {
          throw new Error(`Simulation failed (${response.status}). Check the parameters and try again.`);
        }
        return response.json();
      }

      if (mode === "scenario") {
        const response = await fetch("http://localhost:8000/scenarios/run", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            regimes: scenarioPresets[scenarioIndex].regimes,
            strategy: scenarioStrategy,
            starting_price: startingPrice,
            seed,
            spread,
            order_size: orderSize,
            inventory_risk_factor: riskFactor,
          }),
        });
        if (!response.ok) throw new Error(`Scenario failed (${response.status}). Check the parameters and try again.`);
        setScenario(await response.json());
      } else if (mode === "sweep") {
        if (sweepError) throw new Error(sweepError);
        const response = await fetch("http://localhost:8000/sweeps/run", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            sweep_parameter: sweepParameter,
            sweep_values: parsedSweepValues,
            simulations_per_value: simulationsPerValue,
            starting_seed: startingSeed,
            ticks,
            starting_price: startingPrice,
            volatility,
            buy_pressure: buyPressure,
            order_arrival_rate: orderArrivalRate,
            spread,
            order_size: orderSize,
            inventory_risk_factor: riskFactor,
          }),
        });
        if (!response.ok) throw new Error(`Sweep failed (${response.status}). Check the parameter values and workload limits, then try again.`);
        setSweep(await response.json());
      } else if (mode === "experiment") {
        const response = await fetch("http://localhost:8000/experiments/run", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            ticks,
            starting_price: startingPrice,
            volatility,
            buy_pressure: buyPressure,
            order_arrival_rate: orderArrivalRate,
            spread,
            order_size: orderSize,
            inventory_risk_factor: riskFactor,
            number_of_simulations: numberOfSimulations,
            starting_seed: startingSeed,
          }),
        });
        if (!response.ok) {
          throw new Error(`Experiment failed (${response.status}). Check the parameters and experiment limits, then try again.`);
        }
        setExperiment(await response.json());
      } else if (mode === "comparison") {
        const [basic, inventory] = await Promise.all([
          runStrategy("basic"),
          runStrategy("inventory"),
        ]);
        setComparison({ basic, inventory, seed });
      } else {
        const data = await runStrategy(strategy);
        setResults(data.results);
        setHistory(data.history);
      }
    } catch (error) {
      setError(error instanceof Error ? error.message : "Unable to run the simulation. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  const priceChartData = history
    ? history.midprice.map((price, index) => ({
        tick: index + 1,
        price,
      }))
    : [];

  const pnlChartData = history
    ? history.pnl.map((pnl, index) => ({
        tick: index + 1,
        pnl,
      }))
    : [];

  const inventoryChartData = history
    ? history.inventory.map((inventory, index) => ({
        tick: index + 1,
        inventory,
      }))
    : [];

  const modes = [
    ["single", "Single Strategy", "Run one market maker"],
    ["comparison", "Strategy Comparison", "Compare both strategies"],
    ["experiment", "Multi-Seed Experiment", "Test many market paths"],
    ["sweep", "Parameter Sweep", "Stress-test a parameter"],
    ["scenario", "Scenario Stress Test", "Run changing regimes"],
  ] as const;

  const changeMode = (nextMode: string) => {
    setMode(nextMode);
    setResults(null);
    setHistory(null);
    setComparison(null);
    setExperiment(null);
    setSweep(null);
    setScenario(null);
    setError(null);
  };

  return (
    <main className="min-h-screen bg-[#07090d] text-gray-100">
      <header className="border-b border-white/10 bg-[#0a0d12] px-5 py-5 lg:px-8">
        <div className="mx-auto flex max-w-[1600px] items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-blue-400/30 bg-blue-400/10 font-mono text-sm font-bold text-blue-300">MS</div>
              <h1 className="text-2xl font-semibold tracking-tight">MarketSim</h1>
            </div>
            <p className="mt-1 pl-12 text-sm text-gray-500">Market Making Simulation &amp; Strategy Laboratory</p>
          </div>
          <div className="hidden items-center gap-2 rounded-full border border-emerald-400/20 bg-emerald-400/5 px-3 py-1.5 text-xs text-emerald-300 sm:flex">
            <span className="h-2 w-2 rounded-full bg-emerald-400" />
            Simulation Lab
          </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-[1600px] gap-0 lg:grid-cols-[320px_minmax(0,1fr)]">
        <aside className="border-b border-white/10 bg-[#0a0d12] p-5 lg:min-h-[calc(100vh-86px)] lg:border-b-0 lg:border-r lg:p-6">
          <div className="mb-7">
            <p className="mb-3 text-xs font-semibold uppercase tracking-[0.18em] text-gray-500">Simulation Mode</p>
            <nav className="grid gap-2 sm:grid-cols-2 lg:grid-cols-1">
              {modes.map(([value, label, description]) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => changeMode(value)}
                  className={`rounded-xl border px-3.5 py-3 text-left transition ${
                    mode === value
                      ? "border-blue-400/40 bg-blue-400/10 text-white"
                      : "border-white/5 bg-white/2 text-gray-400 hover:border-white/10 hover:bg-white/4 hover:text-gray-200"
                  }`}
                >
                  <span className="block text-sm font-medium">{label}</span>
                  <span className="mt-0.5 block text-xs text-gray-500">{description}</span>
                </button>
              ))}
            </nav>
          </div>

          <div className="mb-4 flex items-center justify-between">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-gray-500">Configuration</p>
            <span className="rounded-md bg-white/5 px-2 py-1 font-mono text-[10px] uppercase text-gray-500">{mode}</span>
          </div>

          <form onSubmit={(event) => { event.preventDefault(); void runSimulation(); }}>
            <fieldset disabled={loading} className="space-y-5">
          {mode === "comparison" && (
            <p className="text-sm text-gray-500">Compare both strategies with the same parameters and seeded external order flow. Inventory risk applies only to Inventory-Aware.</p>
          )}
          {mode === "experiment" && (
            <>
              <p className="text-sm text-gray-500">Run both strategies for each consecutive seed. Limits: 1–100 seed pairs and 1,000,000 external orders across both strategies. Inventory risk applies only to Inventory-Aware.</p>
              <div>
                <label htmlFor="simulation-count" className="mb-2 block">Number of Simulations</label>
                <input id="simulation-count" type="number" required min="1" max="100" step="1" value={numberOfSimulations} onChange={(event) => setNumberOfSimulations(Number(event.target.value))} className="w-full rounded-lg border border-white/10 bg-[#11161e] p-3 text-sm outline-none transition focus:border-blue-400/50 focus:ring-2 focus:ring-blue-400/10" />
              </div>
              <div>
                <label htmlFor="starting-seed" className="mb-2 block">Starting Seed</label>
                <input id="starting-seed" type="number" required min={Number.MIN_SAFE_INTEGER} max={Number.MAX_SAFE_INTEGER - numberOfSimulations + 1} step="1" value={startingSeed} onChange={(event) => setStartingSeed(Number(event.target.value))} className="w-full rounded-lg border border-white/10 bg-[#11161e] p-3 text-sm outline-none transition focus:border-blue-400/50 focus:ring-2 focus:ring-blue-400/10" />
              </div>
              {2 * numberOfSimulations * ticks * orderArrivalRate > 1000000 && (
                <p role="alert" className="text-red-500">Reduce simulations, ticks, or market activity to stay within the 1,000,000-order limit.</p>
              )}
            </>
          )}
          {mode === "sweep" && (
            <>
              <div>
                <label htmlFor="sweep-parameter" className="mb-2 block">Sweep Parameter</label>
                <select id="sweep-parameter" value={sweepParameter} onChange={(event) => {
                  const parameter = event.target.value as SweepParameter;
                  setSweepParameter(parameter);
                  setSweepValues(sweepParameters[parameter].defaults);
                }} className="w-full rounded-lg border border-white/10 bg-[#11161e] p-3 text-sm outline-none transition focus:border-blue-400/50 focus:ring-2 focus:ring-blue-400/10">
                  {(Object.keys(sweepParameters) as SweepParameter[]).map((parameter) => <option key={parameter} value={parameter}>{sweepParameters[parameter].label}</option>)}
                </select>
              </div>
              <div>
                <label htmlFor="sweep-values" className="mb-2 block">Sweep Values</label>
                <input id="sweep-values" type="text" required value={sweepValues} onChange={(event) => setSweepValues(event.target.value)} aria-describedby="sweep-help" className="w-full rounded-lg border border-white/10 bg-[#11161e] p-3 text-sm outline-none transition focus:border-blue-400/50 focus:ring-2 focus:ring-blue-400/10" />
                <p id="sweep-help" className="mt-2 text-sm text-gray-500">Enter 1–10 comma-separated values. {sweepParameter === "buy_pressure" && "Use fractions: 0.40 means 40%."}</p>
                {sweepParameter === "buy_pressure" && validSweepValues && <p className="text-sm text-gray-500">{parsedSweepValues.map((value) => sweepValueLabel(sweepParameter, value)).join(", ")}</p>}
              </div>
              <div>
                <label htmlFor="simulations-per-value" className="mb-2 block">Simulations Per Value</label>
                <input id="simulations-per-value" type="number" required min="1" max="100" step="1" value={simulationsPerValue} onChange={(event) => setSimulationsPerValue(Number(event.target.value))} className="w-full rounded-lg border border-white/10 bg-[#11161e] p-3 text-sm outline-none transition focus:border-blue-400/50 focus:ring-2 focus:ring-blue-400/10" />
              </div>
              <div>
                <label htmlFor="sweep-starting-seed" className="mb-2 block">Starting Seed</label>
                <input id="sweep-starting-seed" type="number" required min={Number.MIN_SAFE_INTEGER} max={Number.MAX_SAFE_INTEGER - simulationsPerValue + 1} step="1" value={startingSeed} onChange={(event) => setStartingSeed(Number(event.target.value))} className="w-full rounded-lg border border-white/10 bg-[#11161e] p-3 text-sm outline-none transition focus:border-blue-400/50 focus:ring-2 focus:ring-blue-400/10" />
              </div>
              <p className="text-sm text-gray-500">{sweepParameters[sweepParameter].label} is controlled by the sweep; its normal control is disabled. Every point uses the same seed sequence. Limit: 1,000,000 external orders across the whole sweep.</p>
              {sweepParameter === "inventory_risk_factor" && <p className="text-sm text-gray-500">Basic remains an unchanged baseline at every risk factor; only Inventory-Aware is affected.</p>}
              {sweepError && <p role="alert" className="text-red-500">{sweepError}</p>}
            </>
          )}
          {mode === "single" && (
            <div>
              <label className="mb-2 block">
                Strategy
              </label>

              <select
                value={strategy}
                onChange={(e) => setStrategy(e.target.value)}
                className="w-full rounded-lg border border-white/10 bg-[#11161e] p-3 text-sm outline-none transition focus:border-blue-400/50 focus:ring-2 focus:ring-blue-400/10"
              >
                <option value="inventory">
                  Inventory Aware
                </option>

                <option value="basic">
                  Basic
                </option>
              </select>
            </div>
          )}
          {mode === "scenario" && (
            <>
              <div>
                <label htmlFor="scenario" className="mb-2 block">Scenario</label>
                <select id="scenario" value={scenarioIndex} onChange={(event) => setScenarioIndex(Number(event.target.value))} className="w-full rounded-lg border border-white/10 bg-[#11161e] p-3 text-sm outline-none transition focus:border-blue-400/50 focus:ring-2 focus:ring-blue-400/10">
                  {scenarioPresets.map((preset, index) => <option key={preset.name} value={index}>{preset.name}</option>)}
                </select>
              </div>
              <div>
                <label htmlFor="scenario-strategy" className="mb-2 block">Strategy or Comparison</label>
                <select id="scenario-strategy" value={scenarioStrategy} onChange={(event) => setScenarioStrategy(event.target.value)} className="w-full rounded-lg border border-white/10 bg-[#11161e] p-3 text-sm outline-none transition focus:border-blue-400/50 focus:ring-2 focus:ring-blue-400/10">
                  <option value="comparison">Paired Comparison</option>
                  <option value="basic">Basic Market Maker</option>
                  <option value="inventory">Inventory-Aware Market Maker</option>
                </select>
              </div>
              <div className="space-y-3 text-sm">
                <p>{scenarioPresets[scenarioIndex].regimes.map((regime) => regime.name).join(" → ")}</p>
                {scenarioPresets[scenarioIndex].regimes.map((regime, index, regimes) => {
                  const start = 1 + regimes.slice(0, index).reduce((sum, item) => sum + item.duration_ticks, 0);
                  return <p key={index} className="text-gray-500">{regime.name}: ticks {start}–{start + regime.duration_ticks - 1}; volatility {regime.volatility}; buy pressure {(regime.buy_pressure * 100).toFixed(0)}%; {regime.order_arrival_rate} orders/tick.</p>;
                })}
                <p className="text-gray-500">The seeded market process continues across regimes. Inventory risk applies only to Inventory-Aware.</p>
              </div>
            </>
          )}

          <div>
            <label htmlFor="starting-price" className="mb-2 block">Starting Price</label>
            <input id="starting-price" type="number" required min="0.01" step="0.01" value={startingPrice} onChange={(event) => setStartingPrice(Number(event.target.value))} className="w-full rounded-lg border border-white/10 bg-[#11161e] p-3 text-sm outline-none transition focus:border-blue-400/50 focus:ring-2 focus:ring-blue-400/10" />
          </div>
          {mode !== "experiment" && mode !== "sweep" && <div>
            <label htmlFor="seed" className="mb-2 block">Random Seed</label>
            <input id="seed" type="number" required step="1" min={Number.MIN_SAFE_INTEGER} max={Number.MAX_SAFE_INTEGER} value={seed} onChange={(event) => setSeed(Number(event.target.value))} className="w-full rounded-lg border border-white/10 bg-[#11161e] p-3 text-sm outline-none transition focus:border-blue-400/50 focus:ring-2 focus:ring-blue-400/10" />
          </div>}

          {mode !== "scenario" && <>
          <div>
            <label className="mb-2 block">
              Ticks: {ticks}
            </label>

            <input
              type="range"
              min="100"
              max="5000"
              step="100"
              value={ticks}
              onChange={(e) =>
                setTicks(Number(e.target.value))
              }
              className="w-full"
            />
          </div>

          <div>
            <label className="mb-2 block">
              Volatility: {volatility}
            </label>

            <input
              type="range"
              min="0"
              max="10"
              value={volatility}
              disabled={mode === "sweep" && sweepParameter === "volatility"}
              onChange={(e) =>
                setVolatility(Number(e.target.value))
              }
              className="w-full"
            />
          </div>

          <div>
            <label className="mb-2 block">
              Buy Pressure:{" "}
              {(buyPressure * 100).toFixed(0)}%
            </label>

            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={buyPressure}
              disabled={mode === "sweep" && sweepParameter === "buy_pressure"}
              onChange={(e) =>
                setBuyPressure(Number(e.target.value))
              }
              className="w-full"
            />
          </div>

          <div>
            <label className="mb-2 block">
              Market Activity: {orderArrivalRate} orders/tick
            </label>

            <input
              type="range"
              min="1"
              max="10"
              value={orderArrivalRate}
              disabled={mode === "sweep" && sweepParameter === "order_arrival_rate"}
              onChange={(e) =>
                setOrderArrivalRate(Number(e.target.value))
              }
              className="w-full"
            />
          </div>

          </>}

          <div>
            <label className="mb-2 block">
              Spread
            </label>

            <input
              type="number"
              required
              step="0.01"
              min="0.01"
              value={spread}
              disabled={mode === "sweep" && sweepParameter === "spread"}
              onChange={(e) =>
                setSpread(Number(e.target.value))
              }
              className="w-full rounded-lg border border-white/10 bg-[#11161e] p-3 text-sm outline-none transition focus:border-blue-400/50 focus:ring-2 focus:ring-blue-400/10"
            />
          </div>

          <div>
            <label className="mb-2 block">
              Order Size
            </label>

            <input
              type="number"
              required
              min="1"
              value={orderSize}
              onChange={(e) =>
                setOrderSize(Number(e.target.value))
              }
              className="w-full rounded-lg border border-white/10 bg-[#11161e] p-3 text-sm outline-none transition focus:border-blue-400/50 focus:ring-2 focus:ring-blue-400/10"
            />
          </div>

          {(mode !== "single" || strategy === "inventory") && (
            <div>
              <label className="mb-2 block">
                Inventory Risk Factor
              </label>

              <input
                type="number"
                required
                step="0.001"
                min="0"
                value={riskFactor}
                disabled={mode === "sweep" && sweepParameter === "inventory_risk_factor"}
                onChange={(e) =>
                  setRiskFactor(Number(e.target.value))
                }
                className="w-full rounded-lg border border-white/10 bg-[#11161e] p-3 text-sm outline-none transition focus:border-blue-400/50 focus:ring-2 focus:ring-blue-400/10"
              />
            </div>
          )}

          <button
            type="submit"
            disabled={loading || (mode === "sweep" && sweepError !== null) || (mode === "experiment" && 2 * numberOfSimulations * ticks * orderArrivalRate > 1000000)}
            className="w-full rounded-lg bg-blue-500 p-3 font-semibold text-white transition hover:bg-blue-400 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading
              ? "Running..."
              : mode === "scenario" ? "Run Scenario" : mode === "sweep" ? "Run Sweep" : mode === "experiment" ? "Run Experiment" : mode === "comparison" ? "Run Comparison" : "Run Simulation"}
          </button>
            </fieldset>
          </form>
        </aside>

        <section className="min-w-0 p-5 lg:p-8 xl:p-10">
          <div className="mb-8">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-400">Analytics Workspace</p>
            <h2 className="mt-2 text-2xl font-semibold">{modes.find(([value]) => value === mode)?.[1]}</h2>
            <p className="mt-1 text-sm text-gray-500">Configure the market on the left, run the model, and inspect strategy behavior here.</p>
          </div>

      {error && <p role="alert" className="mt-6 text-red-500">{error}</p>}

      {scenario && <ScenarioResults scenario={scenario} />}

      {sweep && <SweepResults sweep={sweep} />}

      {experiment && (
        <section className="space-y-6">
          <h2 className="text-2xl font-semibold">Multi-Seed Experiment Results</h2>
          <p className="text-sm text-gray-500">
            {experiment.config.number_of_simulations} simulations per strategy, {experiment.config.ticks} ticks each.
            Seeds {experiment.config.starting_seed} through {experiment.per_seed[experiment.per_seed.length - 1].seed}.
            P&amp;L statistics use available values only, separately for each strategy, with population standard deviation.
            Inventory and execution statistics include every seed. Gaps indicate unavailable P&amp;L.
          </p>
          <div className="grid gap-6 md:grid-cols-2">
            {(["basic", "inventory"] as const).map((key) => {
              const aggregate = experiment.aggregates[key];
              return (
                <div key={key} className="space-y-5 rounded-2xl border border-white/10 bg-[#0e1219] p-5 text-gray-100">
                  <h3 className={`text-lg font-semibold ${key === "basic" ? "text-blue-400" : "text-amber-400"}`}>
                    {key === "basic" ? "Basic Market Maker" : "Inventory-Aware Market Maker"}
                  </h3>
                  <section className="space-y-2">
                    <h4 className="text-sm font-semibold uppercase text-gray-400">Performance</h4>
                    <p>Average P&amp;L: {currency(aggregate.average_pnl)}</p>
                    <p>P&amp;L Standard Deviation: {currency(aggregate.pnl_standard_deviation)}</p>
                    <p>Best P&amp;L: {currency(aggregate.best_pnl)}</p>
                    <p>Worst P&amp;L: {currency(aggregate.worst_pnl)}</p>
                    <p className="text-sm text-gray-400">Available P&amp;L: {aggregate.valid_pnl_count}; unavailable: {aggregate.unavailable_pnl_count}</p>
                  </section>
                  <section className="space-y-2">
                    <h4 className="text-sm font-semibold uppercase text-gray-400">Inventory Risk</h4>
                    <p>Average Final Inventory: {aggregate.average_final_inventory.toFixed(2)}</p>
                    <p>Average Absolute Inventory: {aggregate.average_absolute_inventory.toFixed(2)}</p>
                    <p>Average Maximum Absolute Inventory: {aggregate.average_maximum_absolute_inventory.toFixed(2)}</p>
                    <p>Worst Maximum Absolute Inventory: {aggregate.worst_maximum_absolute_inventory}</p>
                  </section>
                  <section className="space-y-2">
                    <h4 className="text-sm font-semibold uppercase text-gray-400">Execution</h4>
                    <p>Average MM Fills: {aggregate.average_market_maker_fills.toFixed(2)}</p>
                    <p>Average Executed Volume: {aggregate.average_market_maker_executed_volume.toFixed(2)}</p>
                  </section>
                </div>
              );
            })}
          </div>
          <div className="grid gap-6 lg:grid-cols-2">
            {([
              ["final_pnl", "P&L by Seed"],
              ["maximum_absolute_inventory", "Maximum Absolute Inventory by Seed"],
            ] as const).map(([metric, title]) => (
              <div key={metric}>
                <h3 className="mb-3 text-lg font-medium">{title}</h3>
                <div className="h-80 rounded-2xl border border-white/10 bg-[#0e1219] p-4">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={experiment.per_seed.map((pair) => ({
                      seed: pair.seed,
                      basic: pair.basic[metric],
                      inventory: pair.inventory[metric],
                    }))}>
                      <XAxis dataKey="seed" tickLine={false} />
                      <YAxis domain={["auto", "auto"]} tickLine={false} />
                      <Tooltip labelFormatter={(seed) => `Seed ${seed}`} />
                      <Legend />
                      <Line type="linear" dataKey="basic" name="Basic" stroke="#60a5fa" dot={{ r: 3 }} strokeWidth={2} connectNulls={false} />
                      <Line type="linear" dataKey="inventory" name="Inventory-Aware" stroke="#fbbf24" dot={{ r: 3 }} strokeDasharray="6 3" strokeWidth={2} connectNulls={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {comparison && (
        <section className="space-y-6">
          <h2 className="text-2xl font-semibold">Strategy Comparison Results</h2>
          <p className="text-sm text-gray-500">{comparison.basic.results.ticks} ticks · Seed: {comparison.seed}. Prices reflect each strategy’s order book and may differ.</p>
          <div className="grid gap-6 md:grid-cols-2">
            {(["basic", "inventory"] as const).map((key) => {
              const result = comparison[key].results;
              return (
                <div key={key} className="space-y-2 rounded-2xl border border-white/10 bg-[#0e1219] p-5 text-gray-100">
                  <h3 className={`text-lg font-semibold ${key === "basic" ? "text-blue-400" : "text-amber-400"}`}>
                    {key === "basic" ? "Basic Market Maker" : "Inventory-Aware Market Maker"}
                  </h3>
                  <SimulationMetrics results={result} />
                </div>
              );
            })}
          </div>
          <div className="grid gap-6 lg:grid-cols-2">
            {([
              ["pnl", "Comparison P&L"],
              ["inventory", "Comparison Inventory"],
              ["midprice", "Market Price"],
            ] as const).map(([metric, title]) => (
              <div key={metric} className={metric === "midprice" ? "lg:col-span-2" : ""}>
                <h3 className="mb-3 text-lg font-medium">{title}</h3>
                <div className="h-80 rounded-2xl border border-white/10 bg-[#0e1219] p-4">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={comparison.basic.history[metric].map((value, index) => ({
                      tick: index + 1,
                      basic: value,
                      inventory: comparison.inventory.history[metric][index],
                    }))}>
                      <XAxis dataKey="tick" tickLine={false} />
                      <YAxis domain={["auto", "auto"]} tickLine={false} />
                      <Tooltip labelFormatter={(tick) => `Tick ${tick}`} />
                      <Legend />
                      <Line type="monotone" dataKey="basic" name="Basic" stroke="#60a5fa" dot={false} strokeWidth={2} />
                      <Line type="monotone" dataKey="inventory" name="Inventory-Aware" stroke="#fbbf24" strokeDasharray="6 3" dot={false} strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {results && (
        <div className="space-y-4">
          <h2 className="text-2xl font-semibold">
            Results
          </h2>

          <p>
            Ticks: {results.ticks}
          </p>

          <div className="max-w-md rounded-2xl border border-white/10 bg-[#0e1219] p-5 text-gray-100">
            <SimulationMetrics results={results} />
          </div>
        </div>
      )}

      {history && (
        <div className="mt-10">
          <h2 className="mb-6 text-2xl font-semibold">
            Simulation Analytics
          </h2>

          <div className="grid gap-6 lg:grid-cols-2">
            <div>
              <h3 className="mb-3 text-lg font-medium">
                Market Price
              </h3>

              <div className="h-80 rounded-2xl border border-white/10 bg-[#0e1219] p-4">
                <ResponsiveContainer
                  width="100%"
                  height="100%"
                >
                  <LineChart data={priceChartData}>
                    <XAxis
                      dataKey="tick"
                      tickLine={false}
                    />

                    <YAxis
                      domain={["auto", "auto"]}
                      tickLine={false}
                    />

                    <Tooltip />

                    <Line
                      type="monotone"
                      dataKey="price"
                      dot={false}
                      strokeWidth={2}
                      connectNulls
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div>
              <h3 className="mb-3 text-lg font-medium">
                Inventory
              </h3>

              <div className="h-80 rounded-2xl border border-white/10 bg-[#0e1219] p-4">
                <ResponsiveContainer
                  width="100%"
                  height="100%"
                >
                  <LineChart data={inventoryChartData}>
                    <XAxis
                      dataKey="tick"
                      tickLine={false}
                    />

                    <YAxis
                      domain={["auto", "auto"]}
                      tickLine={false}
                    />

                    <Tooltip />

                    <Line
                      type="monotone"
                      dataKey="inventory"
                      dot={false}
                      strokeWidth={2}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="lg:col-span-2">
              <h3 className="mb-3 text-lg font-medium">
                P&L
              </h3>

              <div className="h-80 rounded-2xl border border-white/10 bg-[#0e1219] p-4">
                <ResponsiveContainer
                  width="100%"
                  height="100%"
                >
                  <LineChart data={pnlChartData}>
                    <XAxis
                      dataKey="tick"
                      tickLine={false}
                    />

                    <YAxis
                      domain={["auto", "auto"]}
                      tickLine={false}
                    />

                    <Tooltip />

                    <Line
                      type="monotone"
                      dataKey="pnl"
                      dot={false}
                      strokeWidth={2}
                      connectNulls
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </div>
      )}
        </section>
      </div>
    </main>
  );
}
