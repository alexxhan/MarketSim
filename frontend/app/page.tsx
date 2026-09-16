"use client";

import { useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
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

function MarketMakerMetrics({ results }: { results: SimulationResults }) {
  return (
    <>
      <p>Total Market Trades: {results.total_market_trades}</p>
      <p>Market Maker Fills: {results.market_maker_fills}</p>
      <p>Market Maker Buy Fills: {results.market_maker_buy_fills}</p>
      <p>Market Maker Sell Fills: {results.market_maker_sell_fills}</p>
      <p>Market Maker Executed Volume: {results.market_maker_executed_volume}</p>
      <p>Average Absolute Inventory: {results.average_absolute_inventory.toFixed(2)}</p>
      <p>Maximum Absolute Inventory: {results.maximum_absolute_inventory}</p>
      <p>P&amp;L per Fill: {results.pnl_per_fill === null ? "Unavailable" : `$${results.pnl_per_fill.toFixed(2)}`}</p>
    </>
  );
}

export default function Home() {
  const [mode, setMode] = useState("single");
  const [strategy, setStrategy] = useState("inventory");
  const [startingPrice, setStartingPrice] = useState(100);
  const [seed, setSeed] = useState(42);
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

  async function runSimulation() {
    setLoading(true);
    setError(null);
    setResults(null);
    setHistory(null);
    setComparison(null);

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

      if (mode === "comparison") {
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

  return (
    <main className="min-h-screen p-10">
      <h1 className="text-4xl font-bold">
        MarketSim
      </h1>

      <p className="mt-2 text-gray-500">
        Market Making Simulator
      </p>

      <form onSubmit={(event) => { event.preventDefault(); void runSimulation(); }} className="mt-10 max-w-md">
        <fieldset disabled={loading} className="space-y-5">
          <div>
            <label htmlFor="mode" className="mb-2 block">Mode</label>
            <select id="mode" value={mode} onChange={(event) => {
              setMode(event.target.value);
              setResults(null);
              setHistory(null);
              setComparison(null);
              setError(null);
            }} className="w-full rounded-lg bg-gray-900 p-3">
              <option value="single">Single Strategy</option>
              <option value="comparison">Strategy Comparison</option>
            </select>
          </div>
          {mode === "comparison" && (
            <p className="text-sm text-gray-500">Compare both strategies with the same parameters and seeded external order flow. Inventory risk applies only to Inventory-Aware.</p>
          )}
          {mode === "single" && (
            <div>
              <label className="mb-2 block">
                Strategy
              </label>

              <select
                value={strategy}
                onChange={(e) => setStrategy(e.target.value)}
                className="w-full rounded-lg bg-gray-900 p-3"
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

          <div>
            <label htmlFor="starting-price" className="mb-2 block">Starting Price</label>
            <input id="starting-price" type="number" required min="0.01" step="0.01" value={startingPrice} onChange={(event) => setStartingPrice(Number(event.target.value))} className="w-full rounded-lg bg-gray-900 p-3" />
          </div>
          <div>
            <label htmlFor="seed" className="mb-2 block">Random Seed</label>
            <input id="seed" type="number" required step="1" min={Number.MIN_SAFE_INTEGER} max={Number.MAX_SAFE_INTEGER} value={seed} onChange={(event) => setSeed(Number(event.target.value))} className="w-full rounded-lg bg-gray-900 p-3" />
          </div>

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
              onChange={(e) =>
                setOrderArrivalRate(Number(e.target.value))
              }
              className="w-full"
            />
          </div>

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
              onChange={(e) =>
                setSpread(Number(e.target.value))
              }
              className="w-full rounded-lg bg-gray-900 p-3"
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
              className="w-full rounded-lg bg-gray-900 p-3"
            />
          </div>

          {(mode === "comparison" || strategy === "inventory") && (
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
                onChange={(e) =>
                  setRiskFactor(Number(e.target.value))
                }
                className="w-full rounded-lg bg-gray-900 p-3"
              />
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-white p-3 font-semibold text-black disabled:opacity-50"
          >
            {loading
              ? "Running..."
              : mode === "comparison" ? "Run Comparison" : "Run Simulation"}
          </button>
        </fieldset>
      </form>

      {error && <p role="alert" className="mt-6 text-red-500">{error}</p>}

      {comparison && (
        <section className="mt-10 max-w-6xl space-y-6">
          <h2 className="text-2xl font-semibold">Strategy Comparison Results</h2>
          <p className="text-sm text-gray-500">{comparison.basic.results.ticks} ticks · Seed: {comparison.seed}. Prices reflect each strategy’s order book and may differ.</p>
          <div className="grid gap-6 md:grid-cols-2">
            {(["basic", "inventory"] as const).map((key) => {
              const result = comparison[key].results;
              return (
                <div key={key} className="space-y-2 rounded-xl bg-gray-900 p-5 text-gray-100">
                  <h3 className={`text-lg font-semibold ${key === "basic" ? "text-blue-400" : "text-amber-400"}`}>
                    {key === "basic" ? "Basic Market Maker" : "Inventory-Aware Market Maker"}
                  </h3>
                  <p>Final P&amp;L: {result.final_pnl === null ? "Unavailable" : `$${result.final_pnl.toFixed(2)}`}</p>
                  <p>Final Inventory: {result.final_inventory}</p>
                  <MarketMakerMetrics results={result} />
                  <p>Final Portfolio Value: {result.final_portfolio_value === null ? "Unavailable" : `$${result.final_portfolio_value.toFixed(2)}`}</p>
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
                <div className="h-80 rounded-xl bg-gray-900 p-4">
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
        <div className="mt-10 space-y-2">
          <h2 className="text-2xl font-semibold">
            Results
          </h2>

          <p>
            Ticks: {results.ticks}
          </p>

          <MarketMakerMetrics results={results} />

          <p>
            Cash: ${results.final_cash.toFixed(2)}
          </p>

          <p>
            Inventory: {results.final_inventory}
          </p>

          <p>
            Portfolio Value:{" "}
            {results.final_portfolio_value !== null
              ? `$${results.final_portfolio_value.toFixed(2)}`
              : "Unavailable"}
          </p>

          <p>
            P&L:{" "}
            {results.final_pnl !== null
              ? `$${results.final_pnl.toFixed(2)}`
              : "Unavailable"}
          </p>

          <p>
            Midprice:{" "}
            {results.final_midprice !== null
              ? `$${results.final_midprice.toFixed(2)}`
              : "Unavailable"}
          </p>
        </div>
      )}

      {history && (
        <div className="mt-12 max-w-6xl">
          <h2 className="mb-6 text-2xl font-semibold">
            Simulation Analytics
          </h2>

          <div className="grid gap-6 lg:grid-cols-2">
            <div>
              <h3 className="mb-3 text-lg font-medium">
                Market Price
              </h3>

              <div className="h-80 rounded-xl bg-gray-900 p-4">
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

              <div className="h-80 rounded-xl bg-gray-900 p-4">
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

              <div className="h-80 rounded-xl bg-gray-900 p-4">
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
    </main>
  );
}
