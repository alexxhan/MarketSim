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
