# MarketSim

MarketSim is an interactive market-making and limit-order-book simulator.

## Planned Features

- Limit order book
- Matching engine
- Simulated market order flow
- Automated market maker
- Inventory-aware quoting
- P&L tracking
- Real-time dashboard
- Strategy comparison
- Market stress scenarios

## Tech Stack

### Frontend
- Next.js
- TypeScript
- Tailwind CSS

### Backend
- Python
- FastAPI

## Status

Work in progress.

## Multi-seed experiments

Select **Multi-Seed Experiment** in the dashboard, or send `POST /experiments/run`:

```json
{
  "number_of_simulations": 10,
  "starting_seed": 42,
  "ticks": 1000,
  "starting_price": 100,
  "volatility": 3,
  "buy_pressure": 0.5,
  "order_arrival_rate": 3,
  "spread": 0.04,
  "order_size": 10,
  "inventory_risk_factor": 0.001
}
```

Each simulation means a pair of independent Basic and Inventory-Aware runs with the same market parameters and seed. Seeds are `starting_seed + index`, beginning at index zero. Inventory risk affects only Inventory-Aware. The existing engine, matching rules, and performance metrics are reused.

The response contains:

- `config`: the effective request parameters.
- `per_seed`: ordered entries `{seed, basic, inventory}`. Each strategy result includes `seed`, `final_pnl`, `final_inventory`, `portfolio_value`, and all existing performance metrics.
- `aggregates`: separate `basic` and `inventory` summaries.
- `aggregation`: the standard-deviation convention and null policy.

P&L aggregates use available P&Ls independently for each strategy. The average is their arithmetic mean; **population** standard deviation is `sqrt(sum((pnl - average_pnl)^2) / valid_pnl_count)`. Best and worst P&L are the maximum and minimum available values. A single available P&L has standard deviation zero. If none are available, all four P&L aggregates are null. `valid_pnl_count` and `unavailable_pnl_count` make the sample sizes explicit. Missing P&L remains null in per-seed results and appears as gaps in the chart; it is never replaced with zero. Strategies can have different valid subsets, so compare their counts alongside the averages.

Inventory and execution averages include every seed. `average_final_inventory` averages signed final inventory. `average_absolute_inventory` averages the runs' mean absolute tick-end inventories. `average_maximum_absolute_inventory` averages their maximum absolute tick-end inventories, and `worst_maximum_absolute_inventory` takes their maximum. Average MM fills and executed volume are arithmetic means of the existing per-run metrics.

Limits are 1–100 simulation pairs, 1–5,000 ticks, and 1–10 external orders per tick. Additionally, `2 * number_of_simulations * ticks * order_arrival_rate` must not exceed 1,000,000. Starting and final seeds must be within JavaScript's safe integer range (−9,007,199,254,740,991 to 9,007,199,254,740,991). Other market parameter limits match the single-run endpoint. Invalid requests return HTTP 422. These limits apply only to experiments; existing simulation requests are unchanged.

## Parameter sweeps and stress testing

Select **Parameter Sweep** or send `POST /sweeps/run`:

```json
{
  "sweep_parameter": "volatility",
  "sweep_values": [1, 2, 3, 4, 5],
  "simulations_per_value": 10,
  "starting_seed": 42,
  "ticks": 1000,
  "starting_price": 100,
  "volatility": 3,
  "buy_pressure": 0.5,
  "order_arrival_rate": 3,
  "spread": 0.04,
  "order_size": 10,
  "inventory_risk_factor": 0.001
}
```

The sweep runner calls the existing multi-seed experiment runner at every point, changing only the selected parameter. Every point uses seeds `starting_seed` through `starting_seed + simulations_per_value - 1` for both strategies. For inventory-risk-factor sweeps, Basic retains the request's baseline risk-factor configuration (which Basic ignores); Inventory-Aware receives the swept value. Basic is still run at every point. No matching, order-flow, strategy, or accounting rules change.

| Parameter | Editable dashboard defaults | Valid values |
| --- | --- | --- |
| `volatility` | 1, 2, 3, 4, 5 | Integers 0–20 |
| `buy_pressure` | 0.40, 0.45, 0.50, 0.55, 0.60 | 0–1; displayed as percentages |
| `order_arrival_rate` | 1, 2, 3, 4, 5 | Integers 1–10 |
| `spread` | 0.02, 0.04, 0.06, 0.08, 0.10 | Greater than zero |
| `inventory_risk_factor` | 0.000, 0.001, 0.002, 0.003, 0.005 | Zero or greater |

Requests accept 1–10 finite numeric sweep values, 1–100 simulation pairs per value, and 1–5,000 ticks per run. Experiment validation applies at every point, including seed bounds. The whole sweep must satisfy `sum(2 * simulations_per_value * ticks * effective_order_arrival_rate)` across its values ≤ 1,000,000. For an activity sweep, each point's swept arrival rate is used. Invalid values, fractional integer parameters, and excessive workloads return HTTP 422 before any simulation runs; values are never clamped.

Responses contain `config`, `sweep_parameter`, `results`, and `aggregation`. Each result is `{value, basic, inventory}`, with the full existing experiment aggregates and valid/missing P&L counts for each strategy. Results retain request order; charts sort by numeric parameter value and use a numeric X axis. Duplicate values remain separate points in the table. P&L statistics retain the experiment's population standard deviation and null policy. Inventory/execution aggregates include every seed; no significance testing is performed.

## Scenario stress tests

Select **Scenario Stress Test**, then choose a preset and Basic, Inventory-Aware, or paired comparison. Each preset lasts 1,000 ticks: Normal for 300, stress for 400, then recovery/normal activity for 300. Normal conditions are volatility 1, buy pressure 50%, and 2 external orders per tick.

| Preset | Stress regime change |
| --- | --- |
| Volatility Shock | Volatility rises to 5 |
| Buy-Side Pressure | Buy pressure rises to 70% |
| Sell-Side Pressure | Buy pressure falls to 30% |
| Liquidity Surge | Order arrival rate rises to 8 per tick |

Other market conditions stay at normal levels. The dashboard previews the regime sequence and exact tick ranges. Results reuse the existing metric groups and show P&L, inventory, and market price with named transition lines. Tooltips identify the regime at each tick.

Custom scenarios use `POST /scenarios/run`:

```json
{
  "strategy": "comparison",
  "starting_price": 100,
  "seed": 42,
  "spread": 0.04,
  "order_size": 10,
  "inventory_risk_factor": 0.001,
  "regimes": [
    {"name": "Normal", "duration_ticks": 300, "volatility": 1, "buy_pressure": 0.5, "order_arrival_rate": 2},
    {"name": "High Volatility", "duration_ticks": 400, "volatility": 5, "buy_pressure": 0.5, "order_arrival_rate": 2},
    {"name": "Recovery", "duration_ticks": 300, "volatility": 1, "buy_pressure": 0.5, "order_arrival_rate": 2}
  ]
}
```

`strategy` accepts `basic`, `inventory`, or `comparison` (default). The response includes the effective `config`, `total_ticks`, `regime_boundaries`, and `runs` keyed by the selected strategies. Each run contains normal `results` (all existing performance metrics) and `history` arrays for `pnl`, `inventory`, `midprice`, `regime_id`, and `regime_name`. Boundary start/end ticks are inclusive and one-based; regime IDs are zero-based list positions, so repeated names remain distinguishable. Null valuations retain their normal meaning and remain gaps in charts.

Each strategy gets one engine and one continuously seeded external order-flow generator for the full scenario. Before the first tick of each regime, only volatility, buy pressure, and orders per tick are updated. The RNG object/state, reference price, order IDs, book, portfolio, and strategy persist. Paired runs use the same seed and regime schedule, so their external order sequence matches even when their books and portfolio outcomes diverge. Existing tick ordering and matching logic are unchanged.

Validation allows 1–10 regimes with nonblank names (up to 80 characters), positive integer durations, at most 5,000 total ticks, integer volatility 0–20, buy pressure 0–1, and integer order arrival rate 1–10. This bounds a paired scenario to 100,000 external orders. Invalid requests return HTTP 422 before execution. Seeds must be integers within JavaScript's safe integer range. Starting price and spread must be positive, order size a positive integer, and inventory risk nonnegative.
