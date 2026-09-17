import { useId, type CSSProperties, type ReactNode } from "react";
import { scenarioPresets } from "../scenarios";
import {
  configurationError,
  isExperiment,
  modes,
  sweepParameters,
  type Configuration,
  type Mode,
  type Strategy,
  type SweepParameter,
} from "../simulation";

function NumberField({
  label,
  value,
  onChange,
  min,
  max,
  step = 1,
  hint,
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
  hint?: string;
}) {
  const id = useId();
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <input
        id={id}
        type="number"
        required
        min={min}
        max={max}
        step={step}
        value={Number.isNaN(value) ? "" : value}
        onChange={(event) => onChange(event.target.value === "" ? NaN : Number(event.target.value))}
        aria-describedby={hint ? `${id}-hint` : undefined}
      />
      {hint && (
        <p id={`${id}-hint`} className="field-hint">
          {hint}
        </p>
      )}
    </div>
  );
}

function RangeField({
  label,
  value,
  onChange,
  min,
  max,
  step = 1,
  display,
  hint,
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
  min: number;
  max: number;
  step?: number;
  display?: string;
  hint: string;
}) {
  const id = useId();
  return (
    <div className="field range-field">
      <div className="field-label">
        <label htmlFor={id}>{label}</label>
        <output htmlFor={id}>{display ?? value}</output>
      </div>
      <input
        id={id}
        type="range"
        style={{ "--range-progress": `${((value - min) / (max - min)) * 100}%` } as CSSProperties}
        min={min}
        max={max}
        step={step}
        value={value}
        aria-valuetext={display}
        aria-describedby={`${id}-hint`}
        onChange={(event) => onChange(Number(event.target.value))}
      />
      <p id={`${id}-hint`} className="field-hint">
        {hint}
      </p>
    </div>
  );
}

function ParameterSection({
  number,
  title,
  description,
  children,
}: {
  number: string;
  title: string;
  description?: string;
  children: ReactNode;
}) {
  return (
    <section className="parameter-section">
      <div className="section-heading">
        <span className="section-number">{number}</span>
        <div>
          <h3>{title}</h3>
          {description && <p>{description}</p>}
        </div>
      </div>
      <div className="parameter-fields">{children}</div>
    </section>
  );
}

export function SimulationTypeSelector({
  mode,
  onChange,
  disabled,
}: {
  mode: Mode;
  onChange: (mode: Mode) => void;
  disabled: boolean;
}) {
  const experiment = isExperiment(mode);
  return (
    <aside className="mode-selector" aria-label={experiment ? "Experiment modes" : "Simulation modes"}>
      <p className="eyebrow">{experiment ? "Experiment type" : "Simulation type"}</p>
      <div className="mode-options">
        {modes
          .filter((item) => isExperiment(item.id) === experiment)
          .map((item) => (
            <button
              type="button"
              key={item.id}
              className={`mode-button ${mode === item.id ? "active" : ""}`}
              aria-pressed={mode === item.id}
              disabled={disabled}
              onClick={() => onChange(item.id)}
            >
              <span className="mode-title">
                {item.label}
                <span aria-hidden="true">{mode === item.id ? "\u2197" : "\u2192"}</span>
              </span>
              <span className="mode-description">{item.description}</span>
            </button>
          ))}
      </div>
    </aside>
  );
}

export function ConfigurationPanel({
  mode,
  config,
  onChange,
  onRun,
  loading,
  error,
}: {
  mode: Mode;
  config: Configuration;
  onChange: (config: Configuration) => void;
  onRun: () => void;
  loading: boolean;
  error: string | null;
}) {
  const update = <K extends keyof Configuration>(key: K, value: Configuration[K]) =>
    onChange({ ...config, [key]: value });
  const selectedMode = modes.find((item) => item.id === mode)!;
  const validation = configurationError(mode, config);
  const hasSeedPairs = mode === "experiment" || mode === "sweep";
  const swept = (parameter: SweepParameter) => mode === "sweep" && config.sweepParameter === parameter;
  const hasInventory =
    mode === "single"
      ? config.strategy === "inventory"
      : mode === "scenario"
        ? config.scenarioStrategy !== "basic"
        : true;
  const preset = scenarioPresets[config.scenarioIndex];
  const totalTicks =
    mode === "scenario"
      ? preset.regimes.reduce((sum, regime) => sum + regime.duration_ticks, 0)
      : config.ticks;
  const runCount =
    mode === "experiment"
      ? 2 * config.numberOfSimulations
      : mode === "sweep"
        ? 2 * config.simulationsPerValue * config.sweepValues.split(",").length
        : mode === "comparison" || (mode === "scenario" && config.scenarioStrategy === "comparison")
          ? 2
          : 1;
  return (
    <form
      className="configuration-panel"
      onSubmit={(event) => {
        event.preventDefault();
        onRun();
      }}
    >
      <div className="panel-heading">
        <div>
          <h2>{selectedMode.label}</h2>
          <p>{selectedMode.description}</p>
        </div>
        <span className="quiet-badge">
          {hasSeedPairs ||
          mode === "comparison" ||
          (mode === "scenario" && config.scenarioStrategy === "comparison")
            ? "Paired strategies"
            : "Single strategy"}
        </span>
      </div>
      <fieldset disabled={loading}>
        {(mode === "single" || mode === "scenario") && (
          <div className="strategy-picker">
            <span className="eyebrow">Strategy</span>
            <div className="segmented" aria-label="Strategy selection">
              {(mode === "scenario"
                ? (["comparison", "basic", "inventory"] as const)
                : (["basic", "inventory"] as const)
              ).map((strategy) => (
                <button
                  type="button"
                  key={strategy}
                  aria-pressed={(mode === "single" ? config.strategy : config.scenarioStrategy) === strategy}
                  onClick={() =>
                    mode === "single"
                      ? update("strategy", strategy as Strategy)
                      : update("scenarioStrategy", strategy)
                  }
                >
                  {strategy === "comparison"
                    ? "Paired Comparison"
                    : strategy === "basic"
                      ? "Basic"
                      : "Inventory-Aware"}
                </button>
              ))}
            </div>
          </div>
        )}
        {isExperiment(mode) && (
          <ParameterSection
            number="01"
            title="Experiment parameters"
            description={
              mode === "scenario"
                ? "A continuous market path through predefined regimes."
                : "Both strategies use the same seed sequence."
            }
          >
            {mode === "experiment" && (
              <>
                <NumberField
                  label="Number of Simulations"
                  value={config.numberOfSimulations}
                  min={1}
                  max={100}
                  onChange={(value) => update("numberOfSimulations", value)}
                  hint="1–100 seed pairs. One run per strategy for each seed."
                />
                <NumberField
                  label="Starting Seed"
                  value={config.startingSeed}
                  min={Number.MIN_SAFE_INTEGER}
                  max={Number.MAX_SAFE_INTEGER - config.numberOfSimulations + 1}
                  onChange={(value) => update("startingSeed", value)}
                  hint="Consecutive seeds, paired across strategies."
                />
              </>
            )}
            {mode === "sweep" && (
              <>
                <div className="field">
                  <label htmlFor="sweep-parameter">Sweep Parameter</label>
                  <select
                    id="sweep-parameter"
                    value={config.sweepParameter}
                    onChange={(event) => {
                      const parameter = event.target.value as SweepParameter;
                      onChange({
                        ...config,
                        sweepParameter: parameter,
                        sweepValues: sweepParameters[parameter].defaults,
                      });
                    }}
                  >
                    {(Object.keys(sweepParameters) as SweepParameter[]).map((parameter) => (
                      <option key={parameter} value={parameter}>
                        {sweepParameters[parameter].label}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="field">
                  <label htmlFor="sweep-values">Sweep Values</label>
                  <input
                    id="sweep-values"
                    required
                    value={config.sweepValues}
                    onChange={(event) => update("sweepValues", event.target.value)}
                    aria-describedby="sweep-hint"
                  />
                  <p id="sweep-hint" className="field-hint">
                    1–10 comma-separated values.
                    {config.sweepParameter === "buy_pressure" && " Use fractions: 0.40 = 40%."}
                  </p>
                </div>
                <NumberField
                  label="Simulations Per Value"
                  value={config.simulationsPerValue}
                  min={1}
                  max={100}
                  onChange={(value) => update("simulationsPerValue", value)}
                  hint="Seed pairs at each parameter value."
                />
                <NumberField
                  label="Starting Seed"
                  value={config.startingSeed}
                  min={Number.MIN_SAFE_INTEGER}
                  max={Number.MAX_SAFE_INTEGER - config.simulationsPerValue + 1}
                  onChange={(value) => update("startingSeed", value)}
                  hint="The sequence is reused at every sweep value."
                />
                <p className="section-note">
                  {sweepParameters[config.sweepParameter].label} is set by the sweep values above.
                  {config.sweepParameter === "inventory_risk_factor" &&
                    " Basic remains an unchanged baseline; only Inventory-Aware is affected."}
                </p>
              </>
            )}
            {mode === "scenario" && (
              <>
                <div className="field full-width">
                  <label htmlFor="scenario">Scenario</label>
                  <select
                    id="scenario"
                    value={config.scenarioIndex}
                    onChange={(event) => update("scenarioIndex", Number(event.target.value))}
                  >
                    {scenarioPresets.map((item, index) => (
                      <option key={item.name} value={index}>
                        {item.name}
                      </option>
                    ))}
                  </select>
                </div>
                <ol className="regime-preview">
                  {preset.regimes.map((regime, index, regimes) => {
                    const start =
                      1 + regimes.slice(0, index).reduce((sum, item) => sum + item.duration_ticks, 0);
                    return (
                      <li key={index}>
                        <span className="eyebrow">
                          Ticks {start}–{start + regime.duration_ticks - 1}
                        </span>
                        <strong>{regime.name}</strong>
                        <span>
                          Volatility {regime.volatility} · Buy {(regime.buy_pressure * 100).toFixed(0)}%
                        </span>
                        <span>{regime.order_arrival_rate} orders / tick</span>
                      </li>
                    );
                  })}
                </ol>
              </>
            )}
          </ParameterSection>
        )}
        <ParameterSection
          number={isExperiment(mode) ? "02" : "01"}
          title="Market environment"
          description={
            mode === "scenario" ? "Regimes control duration, volatility, pressure, and activity." : undefined
          }
        >
          <NumberField
            label="Starting Price"
            value={config.startingPrice}
            min={0.01}
            step={0.01}
            onChange={(value) => update("startingPrice", value)}
          />
          {!hasSeedPairs && (
            <NumberField
              label="Random Seed"
              value={config.seed}
              min={Number.MIN_SAFE_INTEGER}
              max={Number.MAX_SAFE_INTEGER}
              onChange={(value) => update("seed", value)}
              hint="Reuse a seed to reproduce the external order flow."
            />
          )}
          {mode !== "scenario" && (
            <>
              <RangeField
                label="Ticks"
                value={config.ticks}
                min={100}
                max={5000}
                step={100}
                onChange={(value) => update("ticks", value)}
                hint="Simulation duration, measured in discrete steps."
              />
              {!swept("volatility") && (
                <RangeField
                  label="Volatility"
                  value={config.volatility}
                  min={0}
                  max={10}
                  onChange={(value) => update("volatility", value)}
                  hint="Magnitude of synthetic price variation."
                />
              )}
              {!swept("buy_pressure") && (
                <RangeField
                  label="Buy Pressure"
                  value={config.buyPressure}
                  min={0}
                  max={1}
                  step={0.05}
                  display={`${(config.buyPressure * 100).toFixed(0)}%`}
                  onChange={(value) => update("buyPressure", value)}
                  hint="50% balances incoming buy and sell orders."
                />
              )}
              {!swept("order_arrival_rate") && (
                <RangeField
                  label="Market Activity"
                  value={config.orderArrivalRate}
                  min={1}
                  max={10}
                  display={`${config.orderArrivalRate} orders / tick`}
                  onChange={(value) => update("orderArrivalRate", value)}
                  hint="Fixed number of external orders per tick."
                />
              )}
            </>
          )}
        </ParameterSection>
        <ParameterSection number={isExperiment(mode) ? "03" : "02"} title="Strategy parameters">
          {!swept("spread") && (
            <NumberField
              label="Spread"
              value={config.spread}
              min={0.01}
              step={0.01}
              onChange={(value) => update("spread", value)}
              hint="Distance between the bid and ask quotes."
            />
          )}
          <NumberField
            label="Order Size"
            value={config.orderSize}
            min={1}
            onChange={(value) => update("orderSize", value)}
            hint="Units placed on each side of the market."
          />
          {hasInventory && !swept("inventory_risk_factor") && (
            <NumberField
              label="Inventory Risk Factor"
              value={config.riskFactor}
              min={0}
              step={0.001}
              onChange={(value) => update("riskFactor", value)}
              hint="Reservation-price shift per inventory unit. Inventory-Aware only."
            />
          )}
        </ParameterSection>
        {(error || validation) && (
          <div className="inline-error" role="alert">
            <strong>Check this run</strong>
            <p>{error || validation}</p>
          </div>
        )}
        <div className="run-bar">
          <div>
            <strong>
              {totalTicks.toLocaleString()} ticks <span>×</span> {Number.isFinite(runCount) ? runCount : "—"}{" "}
              {runCount === 1 ? "run" : "runs"}
            </strong>
            <p>
              {hasSeedPairs
                ? "Limit: 1,000,000 external orders across both strategies."
                : "Results open in this workspace when the run completes."}
            </p>
          </div>
          <button className="primary-button" type="submit" disabled={loading || !!validation}>
            {loading ? (
              <>
                <span className="spinner" />
                Running…
              </>
            ) : (
              <>
                {selectedMode.action}
                <span aria-hidden="true">→</span>
              </>
            )}
          </button>
        </div>
      </fieldset>
    </form>
  );
}
