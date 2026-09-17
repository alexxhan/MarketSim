from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.simulation.engine import SimulationEngine


class Regime(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=80)
    duration_ticks: int = Field(ge=1, le=5000, strict=True)
    volatility: int = Field(ge=0, le=20, strict=True)
    buy_pressure: float = Field(ge=0, le=1, allow_inf_nan=False, strict=True)
    order_arrival_rate: int = Field(ge=1, le=10, strict=True)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        if not value.strip():
            raise ValueError("Regime name must not be blank")
        return value


def run_scenario(regimes, strategy="comparison", **config):
    boundaries = []
    total_ticks = 0
    for index, regime in enumerate(regimes):
        boundaries.append({
            "regime_id": index,
            "name": regime["name"],
            "start_tick": total_ticks + 1,
            "end_tick": total_ticks + regime["duration_ticks"]
        })
        total_ticks += regime["duration_ticks"]

    runs = {}
    strategies = ("basic", "inventory") if strategy == "comparison" else (strategy,)
    for selected_strategy in strategies:
        first = regimes[0]
        engine = SimulationEngine(
            strategy=selected_strategy,
            volatility=first["volatility"],
            buy_pressure=first["buy_pressure"],
            order_arrival_rate=first["order_arrival_rate"],
            **config
        )
        history = {key: [] for key in ("pnl", "inventory", "midprice", "reference_price", "mark_price", "regime_id", "regime_name")}
        for index, regime in enumerate(regimes):
            engine.volatility = regime["volatility"]
            engine.buy_pressure = regime["buy_pressure"]
            engine.order_arrival_rate = regime["order_arrival_rate"]
            engine.order_flow.volatility = regime["volatility"]
            engine.order_flow.buy_pressure = regime["buy_pressure"]
            for _ in range(regime["duration_ticks"]):
                state = engine.step()
                for metric in ("pnl", "inventory", "midprice", "reference_price", "mark_price"):
                    history[metric].append(state[metric])
                history["regime_id"].append(index)
                history["regime_name"].append(regime["name"])
        runs[selected_strategy] = {
            "results": {
                **state["metrics"],
                "ticks": total_ticks,
                "total_trades": len(engine.trades),
                "final_cash": state["cash"],
                "final_inventory": state["inventory"],
                "final_portfolio_value": state["portfolio_value"],
                "final_pnl": state["pnl"],
                "final_midprice": state["midprice"],
                "final_reference_price": state["reference_price"],
                "final_mark_price": state["mark_price"]
            },
            "history": history
        }
    return {"total_ticks": total_ticks, "regime_boundaries": boundaries, "runs": runs}
