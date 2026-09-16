export type Regime = {
  name: string;
  duration_ticks: number;
  volatility: number;
  buy_pressure: number;
  order_arrival_rate: number;
};

const normal: Regime = {
  name: "Normal", duration_ticks: 300, volatility: 1,
  buy_pressure: 0.5, order_arrival_rate: 2,
};

export const scenarioPresets: { name: string; regimes: Regime[] }[] = [
  {
    name: "Volatility Shock",
    regimes: [normal, { ...normal, name: "High Volatility", duration_ticks: 400, volatility: 5 }, { ...normal, name: "Recovery" }],
  },
  {
    name: "Buy-Side Pressure",
    regimes: [normal, { ...normal, name: "Strong Buy Pressure", duration_ticks: 400, buy_pressure: 0.7 }, { ...normal, name: "Recovery" }],
  },
  {
    name: "Sell-Side Pressure",
    regimes: [normal, { ...normal, name: "Strong Sell Pressure", duration_ticks: 400, buy_pressure: 0.3 }, { ...normal, name: "Recovery" }],
  },
  {
    name: "Liquidity Surge",
    regimes: [normal, { ...normal, name: "High Activity", duration_ticks: 400, order_arrival_rate: 8 }, { ...normal, name: "Normal Activity" }],
  },
];
