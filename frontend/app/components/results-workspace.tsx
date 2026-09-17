import { useState, type ReactNode } from "react";
import { scenarioPresets } from "../scenarios";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  modes,
  sweepParameters,
  sweepValueLabel,
  type ExperimentAggregate,
  type ExperimentResponse,
  type RunResult,
  type ScenarioResponse,
  type SimulationResponse,
  type SimulationResults,
  type Strategy,
  type SweepResponse,
} from "../simulation";

const strategies = ["basic", "inventory"] as const;
const strategyNames = { basic: "Basic", inventory: "Inventory-Aware" };
const colors = { basic: "#75a7f7", inventory: "#dfb56d" };
type MetricGroupName = "Performance" | "Execution" | "Inventory Risk";
type MetricDefinition<T> = {
  key: keyof T;
  label: string;
  group: MetricGroupName;
  format?: "money" | "decimal";
};

const simulationMetrics: MetricDefinition<SimulationResults>[] = [
  { key: "final_pnl", label: "Final P&L", group: "Performance", format: "money" },
  { key: "final_inventory", label: "Final Inventory", group: "Inventory Risk" },
  { key: "final_portfolio_value", label: "Portfolio Value", group: "Performance", format: "money" },
  { key: "market_maker_fills", label: "Market Maker Fills", group: "Execution" },
  { key: "final_cash", label: "Cash", group: "Performance", format: "money" },
  { key: "pnl_per_fill", label: "P&L per Fill", group: "Performance", format: "money" },
  { key: "final_midprice", label: "Final Midprice", group: "Performance", format: "money" },
  { key: "total_market_trades", label: "Total Market Trades", group: "Execution" },
  { key: "total_trades", label: "Total Trades", group: "Execution" },
  { key: "market_maker_buy_fills", label: "Market Maker Buy Fills", group: "Execution" },
  { key: "market_maker_sell_fills", label: "Market Maker Sell Fills", group: "Execution" },
  { key: "market_maker_executed_volume", label: "Executed Volume", group: "Execution" },
  {
    key: "average_absolute_inventory",
    label: "Average Absolute Inventory",
    group: "Inventory Risk",
    format: "decimal",
  },
  { key: "maximum_absolute_inventory", label: "Maximum Absolute Inventory", group: "Inventory Risk" },
];
const aggregateMetrics: MetricDefinition<ExperimentAggregate>[] = [
  { key: "average_pnl", label: "Average P&L", group: "Performance", format: "money" },
  {
    key: "average_final_inventory",
    label: "Average Final Inventory",
    group: "Inventory Risk",
    format: "decimal",
  },
  { key: "pnl_standard_deviation", label: "P&L Standard Deviation", group: "Performance", format: "money" },
  { key: "average_market_maker_fills", label: "Average MM Fills", group: "Execution", format: "decimal" },
  { key: "best_pnl", label: "Best P&L", group: "Performance", format: "money" },
  { key: "worst_pnl", label: "Worst P&L", group: "Performance", format: "money" },
  { key: "valid_pnl_count", label: "Available P&L", group: "Performance" },
  { key: "unavailable_pnl_count", label: "Unavailable P&L", group: "Performance" },
  {
    key: "average_absolute_inventory",
    label: "Average Absolute Inventory",
    group: "Inventory Risk",
    format: "decimal",
  },
  {
    key: "average_maximum_absolute_inventory",
    label: "Average Maximum Absolute Inventory",
    group: "Inventory Risk",
    format: "decimal",
  },
  {
    key: "worst_maximum_absolute_inventory",
    label: "Worst Maximum Absolute Inventory",
    group: "Inventory Risk",
  },
  {
    key: "average_market_maker_executed_volume",
    label: "Average Executed Volume",
    group: "Execution",
    format: "decimal",
  },
];

function formatMetric(value: number | null, format?: "money" | "decimal") {
  if (value === null) return "Unavailable";
  if (format === "money") return value.toLocaleString("en-US", { style: "currency", currency: "USD" });
  return format === "decimal" ? value.toFixed(2) : String(value);
}

type MetricValues = SimulationResults | ExperimentAggregate;
function MetricCard<T extends MetricValues>({
  metric,
  runs,
  emphasis,
}: {
  metric: MetricDefinition<T>;
  runs: { strategy: Strategy; values: T }[];
  emphasis: "primary" | "secondary" | "supporting";
}) {
  return (
    <section className={`metric-card ${emphasis}-metric`}>
      <h3>{metric.label}</h3>
      {runs.map(({ strategy, values }) => (
        <div className="metric-value" key={strategy}>
          <span className={`strategy-name ${strategy}`}>{strategyNames[strategy]}</span>
          <strong>{formatMetric(values[metric.key] as number | null, metric.format)}</strong>
        </div>
      ))}
    </section>
  );
}

function MetricGroup<T extends MetricValues>({
  metrics,
  runs,
}: {
  metrics: MetricDefinition<T>[];
  runs: { strategy: Strategy; values: T }[];
}) {
  return (
    <details className="detailed-analytics">
      <summary>
        Detailed analytics
        <span className="disclosure-action">
          <span className="show-details">Show details</span>
          <span className="hide-details">Hide details</span>
          <span className="disclosure-arrow" aria-hidden="true">
            ↓
          </span>
        </span>
      </summary>
      <div className="metric-groups">
        {(["Performance", "Execution", "Inventory Risk"] as const).map((group) => (
          <section key={group}>
            <h3 className="eyebrow">{group}</h3>
            <table>
              <colgroup>
                <col className="metric-label-column" />
                {runs.map(({ strategy }) => (
                  <col key={strategy} />
                ))}
              </colgroup>
              <thead>
                <tr>
                  <th scope="col">
                    <span className="sr-only">Metric</span>
                  </th>
                  {runs.map(({ strategy }) => (
                    <th scope="col" key={strategy} className={strategy}>
                      {strategyNames[strategy]}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {metrics
                  .filter((metric) => metric.group === group)
                  .map((metric) => (
                    <tr key={String(metric.key)}>
                      <th scope="row">{metric.label}</th>
                      {runs.map(({ strategy, values }) => (
                        <td key={strategy}>
                          {formatMetric(values[metric.key] as number | null, metric.format)}
                        </td>
                      ))}
                    </tr>
                  ))}
              </tbody>
            </table>
          </section>
        ))}
      </div>
    </details>
  );
}

function MetricOverview<T extends MetricValues>({
  metrics,
  runs,
}: {
  metrics: MetricDefinition<T>[];
  runs: { strategy: Strategy; values: T }[];
}) {
  return (
    <div className="metric-overview">
      {metrics.slice(0, 4).map((metric, index) => (
        <MetricCard
          key={String(metric.key)}
          metric={metric}
          runs={runs}
          emphasis={index === 0 ? "primary" : index === 3 ? "supporting" : "secondary"}
        />
      ))}
    </div>
  );
}

type ChartPoint = Record<string, number | null | undefined>;
function ChartCard({
  title,
  subtitle,
  data,
  xKey,
  xLabel,
  series,
  primary = false,
  numeric = false,
  domain,
  xFormatter,
  labelFormatter,
  linear = false,
  dots = false,
  connectNulls = false,
  boundaries = [],
}: {
  title: string;
  subtitle: string;
  data: ChartPoint[];
  xKey: string;
  xLabel: string;
  series: Strategy[];
  primary?: boolean;
  numeric?: boolean;
  domain?: [number | string, number | string];
  xFormatter?: (value: number) => string;
  labelFormatter?: (value: number) => string;
  linear?: boolean;
  dots?: boolean;
  connectNulls?: boolean;
  boundaries?: ScenarioResponse["regime_boundaries"];
}) {
  return (
    <section className={`chart-card ${primary ? "primary-chart" : ""}`} aria-label={title}>
      <div className="chart-heading">
        <div>
          <h3>{title}</h3>
          <p>{subtitle}</p>
        </div>
        <span className="eyebrow">{xLabel}</span>
      </div>
      <div className="chart-canvas">
        <ResponsiveContainer width="100%" height="100%" minWidth={0}>
          <LineChart data={data} margin={{ top: boundaries.length ? 32 : 12, right: 20, left: 8, bottom: 8 }}>
            <CartesianGrid vertical={false} stroke="#26313d" strokeDasharray="3 5" />
            <XAxis
              dataKey={xKey}
              type={numeric ? "number" : "category"}
              domain={domain}
              tickFormatter={xFormatter}
              tickLine={false}
              axisLine={false}
              minTickGap={28}
              tick={{ fill: "#8b98aa", fontSize: 11 }}
              tickMargin={10}
            />
            <YAxis
              domain={["auto", "auto"]}
              tickLine={false}
              axisLine={false}
              width={70}
              tick={{ fill: "#8b98aa", fontSize: 11 }}
              tickFormatter={(value: number) =>
                new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 2 }).format(
                  value,
                )
              }
            />
            <Tooltip
              contentStyle={{
                background: "#171e28",
                border: "1px solid #354252",
                borderRadius: 6,
                fontSize: 12,
                color: "#e6edf5",
              }}
              labelStyle={{ color: "#a9b6c7", marginBottom: 6 }}
              labelFormatter={(value) =>
                labelFormatter ? labelFormatter(Number(value)) : `${xLabel} ${value}`
              }
              formatter={(value, name) => [
                typeof value === "number"
                  ? value.toLocaleString("en-US", { maximumFractionDigits: 6 })
                  : value,
                name,
              ]}
            />
            <Legend iconType="plainline" iconSize={18} wrapperStyle={{ fontSize: 11, paddingTop: 12 }} />
            {boundaries.slice(1).map((regime) => (
              <ReferenceLine
                key={regime.regime_id}
                x={regime.start_tick}
                stroke="#8b98aa"
                strokeDasharray="4 4"
                label={{
                  className: regime.regime_id % 2 === 0 ? "regime-label-alternate" : undefined,
                  value: `${regime.name} (${regime.start_tick})`,
                  position: "top",
                  fill: "#a9b6c7",
                  fontSize: 10,
                }}
              />
            ))}
            {series.map((strategy) => (
              <Line
                key={strategy}
                type={linear ? "linear" : "monotone"}
                dataKey={strategy}
                name={strategyNames[strategy]}
                stroke={colors[strategy]}
                strokeDasharray={strategy === "inventory" && series.length > 1 ? "6 3" : undefined}
                dot={dots ? { r: 3 } : false}
                activeDot={{ r: 4 }}
                strokeWidth={2}
                connectNulls={connectNulls}
                isAnimationActive={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}

function SimulationAnalytics({
  runs,
  scenario,
  single = false,
}: {
  runs: Partial<Record<Strategy, SimulationResponse>>;
  scenario?: ScenarioResponse;
  single?: boolean;
}) {
  const present = strategies.filter((strategy) => runs[strategy]);
  const values = present.map((strategy) => ({ strategy, values: runs[strategy]!.results }));
  return (
    <>
      <MetricOverview metrics={simulationMetrics} runs={values} />
      {scenario && (
        <ol className="regime-strip">
          {scenario.regime_boundaries.map((regime) => (
            <li key={regime.regime_id}>
              <span>{regime.name}</span>
              <small>
                Ticks {regime.start_tick}–{regime.end_tick}
              </small>
            </li>
          ))}
        </ol>
      )}
      <div className="chart-grid">
        {(
          [
            ["pnl", "P&L", "Mark-to-market portfolio performance"],
            ["inventory", "Inventory Exposure", "Position held through the market path"],
            ["midprice", "Market Price", "Order-book midprice"],
          ] as const
        ).map(([metric, title, subtitle]) => (
          <ChartCard
            key={metric}
            title={title}
            subtitle={subtitle}
            primary={metric === "pnl"}
            data={Array.from({ length: runs[present[0]]!.history[metric].length }, (_, index) => ({
              tick: index + 1,
              ...Object.fromEntries(
                present.map((strategy) => [strategy, runs[strategy]!.history[metric][index]]),
              ),
            }))}
            xKey="tick"
            xLabel="Tick"
            series={present}
            numeric={!!scenario}
            domain={scenario ? [1, scenario.total_ticks] : undefined}
            linear={!!scenario}
            connectNulls={single && metric !== "inventory"}
            boundaries={scenario?.regime_boundaries}
            labelFormatter={
              scenario
                ? (tick) =>
                    `Tick ${tick} · ${scenario.regime_boundaries.find((regime) => tick >= regime.start_tick && tick <= regime.end_tick)?.name ?? ""}`
                : undefined
            }
          />
        ))}
      </div>
      <p className="analytics-note">
        {single
          ? "Values are marked to the current order-book midprice."
          : "Each strategy has its own order-book midprice; prices may differ despite identical external order flow."}{" "}
        P&amp;L and midprice may be unavailable when the book is not two-sided.
      </p>
      <MetricGroup metrics={simulationMetrics} runs={values} />
    </>
  );
}

const aggregationNote =
  "P&L statistics exclude unavailable values separately for each strategy and use population standard deviation. Inventory and execution statistics include every seed. Chart gaps indicate unavailable P&L.";

function ExperimentResults({ experiment }: { experiment: ExperimentResponse }) {
  const runs = strategies.map((strategy) => ({ strategy, values: experiment.aggregates[strategy] }));
  return (
    <>
      <MetricOverview metrics={aggregateMetrics} runs={runs} />
      <div className="chart-grid">
        {(
          [
            ["final_pnl", "P&L by Seed"],
            ["maximum_absolute_inventory", "Maximum Absolute Inventory by Seed"],
          ] as const
        ).map(([metric, title]) => (
          <ChartCard
            key={metric}
            title={title}
            subtitle="Paired strategies on each seeded market path"
            primary
            data={experiment.per_seed.map((pair) => ({
              seed: pair.seed,
              basic: pair.basic[metric],
              inventory: pair.inventory[metric],
            }))}
            xKey="seed"
            xLabel="Seed"
            series={[...strategies]}
            linear
            dots
          />
        ))}
      </div>
      <p className="analytics-note">{aggregationNote}</p>
      <MetricGroup metrics={aggregateMetrics} runs={runs} />
    </>
  );
}

function SweepResults({ sweep }: { sweep: SweepResponse }) {
  const [group, setGroup] = useState<MetricGroupName>("Performance");
  const parameter = sweep.sweep_parameter;
  const label = sweepParameters[parameter].label;
  const chartPoints = [...sweep.results].sort((a, b) => a.value - b.value);
  const columns = aggregateMetrics.filter((metric) => metric.group === group);
  return (
    <>
      <div className="sweep-summary">
        <div>
          <span className="eyebrow">Parameter under test</span>
          <strong>{label}</strong>
        </div>
        <div>
          <span className="eyebrow">Values</span>
          <strong>{sweep.results.map((point) => sweepValueLabel(parameter, point.value)).join(" / ")}</strong>
        </div>
        <div>
          <span className="eyebrow">Seed pairs per value</span>
          <strong>{sweep.config.simulations_per_value}</strong>
        </div>
      </div>
      <div className="chart-grid">
        {(
          [
            ["average_pnl", "Average P&L"],
            ["pnl_standard_deviation", "P&L Standard Deviation"],
            ["average_absolute_inventory", "Average Absolute Inventory"],
            ["average_market_maker_fills", "Average Market Maker Fills"],
          ] as const
        ).map(([metric, title]) => (
          <ChartCard
            key={metric}
            title={title}
            subtitle={`Response to ${label.toLowerCase()}`}
            primary={metric === "average_pnl"}
            data={chartPoints.map((point) => ({
              value: point.value,
              basic: point.basic[metric],
              inventory: point.inventory[metric],
            }))}
            xKey="value"
            xLabel={label}
            series={[...strategies]}
            numeric
            domain={["dataMin", "dataMax"]}
            xFormatter={(value) => sweepValueLabel(parameter, value)}
            labelFormatter={(value) => `${label}: ${sweepValueLabel(parameter, value)}`}
            linear
            dots
          />
        ))}
      </div>
      <section className="sweep-table-card">
        <div className="table-heading">
          <div>
            <h3>Parameter comparison</h3>
            <p>All values, grouped by metric family. Scroll the table to inspect additional columns.</p>
          </div>
          <div className="segmented" aria-label="Sweep metrics">
            {(["Performance", "Execution", "Inventory Risk"] as const).map((item) => (
              <button type="button" key={item} aria-pressed={group === item} onClick={() => setGroup(item)}>
                {item}
              </button>
            ))}
          </div>
        </div>
        <div className="table-scroll" tabIndex={0} role="region" aria-label={`${group} sweep comparison`}>
          <table className="sweep-table">
            <thead>
              <tr>
                <th scope="col">{label}</th>
                <th scope="col">Strategy</th>
                {columns.map((metric) => (
                  <th key={metric.key} scope="col">
                    {metric.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sweep.results.map((point, index) =>
                strategies.map((strategy, strategyIndex) => (
                  <tr key={`${index}-${strategy}`} className={strategyIndex === 0 ? "pair-start" : ""}>
                    {strategyIndex === 0 && (
                      <th scope="rowgroup" rowSpan={2} className="parameter-value">
                        {sweepValueLabel(parameter, point.value)}
                      </th>
                    )}
                    <th scope="row" className={strategy}>
                      {strategyNames[strategy]}
                    </th>
                    {columns.map((metric) => (
                      <td key={metric.key}>{formatMetric(point[strategy][metric.key], metric.format)}</td>
                    ))}
                  </tr>
                )),
              )}
            </tbody>
          </table>
        </div>
      </section>
      <p className="analytics-note">
        {aggregationNote}
        {parameter === "inventory_risk_factor" &&
          " Basic is an unchanged baseline; only Inventory-Aware responds to the risk factor."}
      </p>
    </>
  );
}

export function ResultsWorkspace({ result, onAdjust }: { result: RunResult; onAdjust: () => void }) {
  const c = result.configuration;
  const seedPairs = result.mode === "experiment" || result.mode === "sweep";
  const count = result.mode === "experiment" ? c.numberOfSimulations : c.simulationsPerValue;
  const ticks = result.mode === "scenario" ? result.data.total_ticks : c.ticks;
  let analytics: ReactNode;
  switch (result.mode) {
    case "single":
      analytics = <SimulationAnalytics runs={{ [c.strategy]: result.data }} single />;
      break;
    case "comparison":
      analytics = <SimulationAnalytics runs={result.data} />;
      break;
    case "scenario":
      analytics = <SimulationAnalytics runs={result.data.runs} scenario={result.data} />;
      break;
    case "experiment":
      analytics = <ExperimentResults experiment={result.data} />;
      break;
    case "sweep":
      analytics = <SweepResults sweep={result.data} />;
      break;
  }
  return (
    <div className="results-workspace">
      <div className="workspace-heading">
        <div>
          <p className="eyebrow">Completed run</p>
          <h2>{modes.find((mode) => mode.id === result.mode)!.label}</h2>
          <p>
            {result.mode === "scenario" && (
              <>
                {scenarioPresets[c.scenarioIndex].name}
                <span>·</span>
              </>
            )}
            {ticks.toLocaleString()} ticks <span>·</span>{" "}
            {seedPairs ? `Seeds ${c.startingSeed}–${c.startingSeed + count - 1}` : `Seed ${c.seed}`}{" "}
            <span>·</span>{" "}
            {seedPairs
              ? "Paired strategy comparison"
              : result.mode === "single"
                ? strategyNames[c.strategy]
                : result.mode === "scenario" && c.scenarioStrategy !== "comparison"
                  ? strategyNames[c.scenarioStrategy]
                  : "Basic / Inventory-Aware"}
          </p>
        </div>
        <button type="button" className="secondary-button" onClick={onAdjust}>
          Edit Configuration<span aria-hidden="true">↗</span>
        </button>
      </div>
      {analytics}
    </div>
  );
}

export function EmptyResults({ onConfigure }: { onConfigure: () => void }) {
  return (
    <div className="empty-results">
      <div className="empty-symbol" aria-hidden="true">
        ∑
      </div>
      <p className="eyebrow">Analytics workspace</p>
      <h2>Your first market path starts here.</h2>
      <p>
        Run a simulation or experiment to explore P&amp;L, inventory exposure, and execution. Results will
        appear here.
      </p>
      <button type="button" className="primary-button" onClick={onConfigure}>
        Configure a simulation<span aria-hidden="true">→</span>
      </button>
    </div>
  );
}
