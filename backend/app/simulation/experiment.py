from statistics import mean, pstdev

from app.simulation.engine import SimulationEngine
from app.market.validation import finite_number, SimulationDomainError


def aggregate_results(results):
    if not results:
        raise SimulationDomainError("An experiment requires complete paired results")
    pnl_values = [finite_number(result["final_pnl"], "Final P&L") for result in results]
    return {
        "valid_pnl_count": len(pnl_values),
        "unavailable_pnl_count": 0,
        "average_pnl": mean(pnl_values),
        "pnl_standard_deviation": pstdev(pnl_values),
        "best_pnl": max(pnl_values),
        "worst_pnl": min(pnl_values),
        "average_final_inventory": mean(result["final_inventory"] for result in results),
        "average_absolute_inventory": mean(result["average_absolute_inventory"] for result in results),
        "average_maximum_absolute_inventory": mean(result["maximum_absolute_inventory"] for result in results),
        "worst_maximum_absolute_inventory": max(result["maximum_absolute_inventory"] for result in results),
        "average_market_maker_fills": mean(result["market_maker_fills"] for result in results),
        "average_market_maker_executed_volume": mean(result["market_maker_executed_volume"] for result in results)
    }


def run_experiment(number_of_simulations, starting_seed, ticks, *, basic_inventory_risk_factor=None, **market_config):
    per_seed = []
    for seed in range(starting_seed, starting_seed + number_of_simulations):
        pair = {"seed": seed}
        for strategy in ("basic", "inventory"):
            strategy_config = dict(market_config)
            if strategy == "basic" and basic_inventory_risk_factor is not None:
                strategy_config["inventory_risk_factor"] = basic_inventory_risk_factor
            try:
                engine = SimulationEngine(strategy=strategy, seed=seed, **strategy_config)
                for _ in range(ticks):
                    state = engine.step()
            except SimulationDomainError as error:
                raise SimulationDomainError(f"Experiment stopped at seed {seed} ({strategy}): {error}") from error
            pair[strategy] = {
                "seed": seed,
                "final_pnl": state["pnl"],
                "final_inventory": state["inventory"],
                "portfolio_value": state["portfolio_value"],
                "final_reference_price": state["reference_price"],
                "final_mark_price": state["mark_price"],
                **state["metrics"]
            }
        per_seed.append(pair)
    return {
        "per_seed": per_seed,
        "aggregates": {
            strategy: aggregate_results([pair[strategy] for pair in per_seed])
            for strategy in ("basic", "inventory")
        },
        "aggregation": {
            "pnl_standard_deviation": "population",
            "pnl_null_handling": "Every statistic includes every paired seed. A domain failure rejects the entire experiment; no partial aggregates are returned."
        }
    }
