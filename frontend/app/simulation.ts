import { scenarioPresets, type Regime } from "./scenarios";

export type SimulationResults = {
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
  final_portfolio_value: number;
  final_pnl: number;
  final_midprice: number | null;
  final_reference_price: number;
  final_mark_price: number;
};

export type SimulationHistory = {
  pnl: number[];
  reference_price: number[];
  mark_price: number[];
  inventory: number[];
  midprice: (number | null)[];
};

export type SimulationResponse = {
  results: SimulationResults;
  history: SimulationHistory;
};

export type Comparison = {
  basic: SimulationResponse;
  inventory: SimulationResponse;
  seed: number;
};

export type ExperimentAggregate = {
  valid_pnl_count: number;
  unavailable_pnl_count: number;
  average_pnl: number;
  pnl_standard_deviation: number;
  best_pnl: number;
  worst_pnl: number;
  average_final_inventory: number;
  average_absolute_inventory: number;
  average_maximum_absolute_inventory: number;
  worst_maximum_absolute_inventory: number;
  average_market_maker_fills: number;
  average_market_maker_executed_volume: number;
};

export type ExperimentSeedResult = {
  final_pnl: number;
  maximum_absolute_inventory: number;
};

export type ExperimentResponse = {
  config: { number_of_simulations: number; starting_seed: number; ticks: number };
  per_seed: { seed: number; basic: ExperimentSeedResult; inventory: ExperimentSeedResult }[];
  aggregates: { basic: ExperimentAggregate; inventory: ExperimentAggregate };
};

export type ScenarioResponse = {
  config: { regimes: Regime[]; seed: number; strategy: string };
  total_ticks: number;
  regime_boundaries: { regime_id: number; name: string; start_tick: number; end_tick: number }[];
  runs: Partial<
    Record<
      "basic" | "inventory",
      {
        results: SimulationResults;
        history: SimulationHistory & { regime_id: number[]; regime_name: string[] };
      }
    >
  >;
};

export const sweepParameters = {
  volatility: { label: "Volatility", defaults: "1, 2, 3, 4, 5" },
  buy_pressure: { label: "Buy Pressure", defaults: "0.40, 0.45, 0.50, 0.55, 0.60" },
  order_arrival_rate: { label: "Market Activity", defaults: "1, 2, 3, 4, 5" },
  spread: { label: "Spread", defaults: "0.02, 0.04, 0.06, 0.08, 0.10" },
  inventory_risk_factor: { label: "Inventory Risk Factor", defaults: "0.000, 0.001, 0.002, 0.003, 0.005" },
};

export type SweepParameter = keyof typeof sweepParameters;
export type SweepResponse = {
  config: { simulations_per_value: number; starting_seed: number; ticks: number };
  sweep_parameter: SweepParameter;
  results: { value: number; basic: ExperimentAggregate; inventory: ExperimentAggregate }[];
};

export type Strategy = "basic" | "inventory";
export type Mode = "single" | "comparison" | "experiment" | "sweep" | "scenario";
export type View = "simulation" | "experiments" | "results";

export const modes: { id: Mode; label: string; description: string; action: string }[] = [
  {
    id: "single",
    label: "Single Strategy",
    description: "Inspect one market maker over a seeded market path.",
    action: "Run Simulation",
  },
  {
    id: "comparison",
    label: "Strategy Comparison",
    description: "Compare both strategies under identical external order flow.",
    action: "Run Comparison",
  },
  {
    id: "experiment",
    label: "Multi-Seed Experiment",
    description: "Measure both strategies across paired market paths.",
    action: "Run Experiment",
  },
  {
    id: "sweep",
    label: "Parameter Sweep",
    description: "Vary one parameter across the same sequence of seeds.",
    action: "Run Sweep",
  },
  {
    id: "scenario",
    label: "Scenario Stress Test",
    description: "Observe strategy behavior as market regimes change.",
    action: "Run Scenario",
  },
];

export type Configuration = {
  strategy: Strategy;
  scenarioIndex: number;
  scenarioStrategy: Strategy | "comparison";
  startingPrice: number;
  seed: number;
  startingSeed: number;
  numberOfSimulations: number;
  sweepParameter: SweepParameter;
  sweepValues: string;
  simulationsPerValue: number;
  ticks: number;
  volatility: number;
  buyPressure: number;
  orderArrivalRate: number;
  spread: number;
  orderSize: number;
  riskFactor: number;
};

export const initialConfiguration: Configuration = {
  strategy: "inventory",
  scenarioIndex: 0,
  scenarioStrategy: "comparison",
  startingPrice: 100,
  seed: 42,
  startingSeed: 42,
  numberOfSimulations: 10,
  sweepParameter: "volatility",
  sweepValues: sweepParameters.volatility.defaults,
  simulationsPerValue: 10,
  ticks: 1000,
  volatility: 3,
  buyPressure: 0.5,
  orderArrivalRate: 3,
  spread: 0.04,
  orderSize: 10,
  riskFactor: 0.001,
};

export type RunResult = { configuration: Configuration } & (
  | { mode: "single"; data: SimulationResponse }
  | { mode: "comparison"; data: Comparison }
  | { mode: "experiment"; data: ExperimentResponse }
  | { mode: "sweep"; data: SweepResponse }
  | { mode: "scenario"; data: ScenarioResponse }
);

export function isExperiment(mode: Mode) {
  return mode === "experiment" || mode === "sweep" || mode === "scenario";
}

export function sweepValueLabel(parameter: SweepParameter, value: number) {
  return parameter === "buy_pressure" ? `${Number((value * 100).toFixed(6))}%` : String(value);
}

export function configurationError(mode: Mode, config: Configuration): string | null {
  if (
    mode === "experiment" &&
    2 * config.numberOfSimulations * config.ticks * config.orderArrivalRate > 1000000
  ) {
    return "Reduce simulations, ticks, or market activity to stay within the 1,000,000-order limit.";
  }
  if (mode !== "sweep") return null;
  const tokens = config.sweepValues.split(",").map((value) => value.trim());
  const values = tokens.map(Number);
  const valid =
    tokens.length <= 10 &&
    tokens.every((value) => value !== "") &&
    values.every((value) => {
      if (!Number.isFinite(value)) return false;
      if (config.sweepParameter === "volatility") return Number.isInteger(value) && value >= 0 && value <= 20;
      if (config.sweepParameter === "order_arrival_rate")
        return Number.isInteger(value) && value >= 1 && value <= 10;
      if (config.sweepParameter === "buy_pressure") return value >= 0 && value <= 1;
      if (config.sweepParameter === "spread") return value > 0;
      return value >= 0;
    });
  if (!valid)
    return "Enter 1–10 values: volatility integers 0–20; activity integers 1–10; buy pressure 0–1; spread > 0; risk factor ≥ 0.";
  const workload =
    2 *
    config.simulationsPerValue *
    config.ticks *
    values.reduce(
      (sum, value) =>
        sum + (config.sweepParameter === "order_arrival_rate" ? value : config.orderArrivalRate),
      0,
    );
  return workload > 1000000
    ? "Reduce sweep values, simulations, ticks, or market activity to stay within 1,000,000 external orders."
    : null;
}

export const API_URL = "http://localhost:8000";

async function post<T>(path: string, body: object): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    throw new Error("Cannot reach the simulation API. Check that the backend is running, then try again.");
  }
  if (!response.ok) {
    if (response.status === 422) {
      const error: { detail?: unknown } = await response.json().catch(() => ({}));
      if (typeof error.detail === "string") throw new Error(error.detail);
    }
    throw new Error(
      response.status === 422
        ? "The run could not start. Check the parameter values and workload limits, then try again."
        : "The simulation API could not complete this run. Please try again.",
    );
  }
  try {
    return (await response.json()) as T;
  } catch {
    throw new Error("The simulation API returned an unreadable result. Please try again.");
  }
}

export async function runSimulation(mode: Mode, configuration: Configuration): Promise<RunResult> {
  const error = configurationError(mode, configuration);
  if (error) throw new Error(error);
  const c = configuration;
  const market = {
    ticks: c.ticks,
    starting_price: c.startingPrice,
    volatility: c.volatility,
    buy_pressure: c.buyPressure,
    order_arrival_rate: c.orderArrivalRate,
    spread: c.spread,
    order_size: c.orderSize,
  };
  const runStrategy = (strategy: Strategy) =>
    post<SimulationResponse>("/simulation/run", {
      ...market,
      seed: c.seed,
      strategy,
      ...(strategy === "inventory" ? { inventory_risk_factor: c.riskFactor } : {}),
    });
  switch (mode) {
    case "single":
      return { mode, configuration, data: await runStrategy(c.strategy) };
    case "comparison": {
      const [basic, inventory] = await Promise.all([runStrategy("basic"), runStrategy("inventory")]);
      return { mode, configuration, data: { basic, inventory, seed: c.seed } };
    }
    case "experiment":
      return {
        mode,
        configuration,
        data: await post<ExperimentResponse>("/experiments/run", {
          ...market,
          inventory_risk_factor: c.riskFactor,
          number_of_simulations: c.numberOfSimulations,
          starting_seed: c.startingSeed,
        }),
      };
    case "sweep":
      return {
        mode,
        configuration,
        data: await post<SweepResponse>("/sweeps/run", {
          ...market,
          inventory_risk_factor: c.riskFactor,
          sweep_parameter: c.sweepParameter,
          sweep_values: c.sweepValues.split(",").map(Number),
          simulations_per_value: c.simulationsPerValue,
          starting_seed: c.startingSeed,
        }),
      };
    case "scenario":
      return {
        mode,
        configuration,
        data: await post<ScenarioResponse>("/scenarios/run", {
          regimes: scenarioPresets[c.scenarioIndex].regimes,
          strategy: c.scenarioStrategy,
          starting_price: c.startingPrice,
          seed: c.seed,
          spread: c.spread,
          order_size: c.orderSize,
          inventory_risk_factor: c.riskFactor,
        }),
      };
  }
}
